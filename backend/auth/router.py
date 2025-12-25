import os
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import User
from backend.auth.schemas import (
    UserRegisterRequest,
    UserRegisterResponse,
    UserLoginRequest,
    UserLoginResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
)
from backend.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    generate_verification_token,
)
from backend.auth.email_service import send_verification_email
from backend.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


@router.post("/register", response_model=UserRegisterResponse)
async def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """Register a new user and send email verification."""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Generate verification token
    verification_token = generate_verification_token()
    verification_token_expires = datetime.utcnow() + timedelta(hours=24)

    # Create new user
    new_user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        first_name=request.first_name,
        last_name=request.last_name,
        verification_token=verification_token,
        verification_token_expires=verification_token_expires,
        is_active=False,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Send verification email (async in background)
    await send_verification_email(new_user.email, verification_token)

    # Prepare response
    verification_url = f"{FRONTEND_URL}/verify-email?token={verification_token}"

    return UserRegisterResponse(
        email=new_user.email,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        user_id=new_user.user_id,
        is_active=new_user.is_active,
        is_verified=new_user.is_verified,
        is_superuser=new_user.is_superuser,
        subscription_tier=new_user.subscription_tier,
        subscription_status=new_user.subscription_status,
        subscription_start_date=new_user.subscription_start_date,
        subscription_end_date=new_user.subscription_end_date,
        trial_end_date=new_user.trial_end_date,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at,
        last_login=new_user.last_login,
        verification_url=verification_url,
    )


@router.post("/verify-email", response_model=VerifyEmailResponse)
async def verify_email(request: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Verify user email with token."""
    user = db.query(User).filter(User.verification_token == request.token).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )

    # Check if token expired
    if user.verification_token_expires and user.verification_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token expired"
        )

    # Verify user
    user.is_verified = True
    user.is_active = True
    user.verification_token = None
    user.verification_token_expires = None

    db.commit()
    db.refresh(user)

    logger.info(f"User {user.email} verified successfully")

    return VerifyEmailResponse(
        message="Email verified successfully",
        email=user.email,
        is_verified=user.is_verified,
    )


@router.post("/login", response_model=UserLoginResponse)
async def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """Login user and return JWT access token."""
    user = db.query(User).filter(User.email == request.email).first()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is inactive"
        )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Create access token
    access_token = create_access_token(data={"sub": str(user.user_id)})

    logger.info(f"User {user.email} logged in successfully")

    return UserLoginResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "user_id": str(user.user_id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_verified": user.is_verified,
            "subscription_tier": user.subscription_tier.value,
        }
    )


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return {
        "user_id": str(current_user.user_id),
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "is_verified": current_user.is_verified,
        "is_active": current_user.is_active,
        "is_superuser": current_user.is_superuser,
        "subscription_tier": current_user.subscription_tier.value,
        "subscription_status": current_user.subscription_status.value,
        "preferred_language": getattr(current_user, 'preferred_language', 'fr'),
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
    }


@router.patch("/me/language")
async def update_language(
    language: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user's preferred language.

    Args:
        language: Language code ('fr' or 'en')
    """
    from backend.utils.i18n import validate_language, get_success_message, get_error_message

    # Validate language
    try:
        validated_language = validate_language(language)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=get_error_message("invalid_language", language)
        )

    # Update user's preferred language
    current_user.preferred_language = validated_language
    db.commit()
    db.refresh(current_user)

    logger.info(f"Updated language preference for user {current_user.email} to {validated_language}")

    return {
        "message": get_success_message("language_updated", validated_language),
        "preferred_language": validated_language
    }
