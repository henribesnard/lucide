from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from uuid import UUID

from backend.db.models import SubscriptionTier, SubscriptionStatus


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str


class UserRegisterResponse(BaseModel):
    email: str
    first_name: str
    last_name: str
    user_id: UUID
    is_active: bool
    is_verified: bool
    is_superuser: bool
    subscription_tier: SubscriptionTier
    subscription_status: SubscriptionStatus
    subscription_start_date: datetime
    subscription_end_date: Optional[datetime]
    trial_end_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    verification_url: str

    class Config:
        from_attributes = True


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


class VerifyEmailRequest(BaseModel):
    token: str


class VerifyEmailResponse(BaseModel):
    message: str
    email: str
    is_verified: bool
