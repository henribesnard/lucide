#!/usr/bin/env python3
"""Create a test user and generate a JWT token."""
import asyncio
import sys
from datetime import timedelta

from sqlalchemy import select
from backend.auth.security import create_access_token, hash_password
from backend.db.database import AsyncSessionLocal
from backend.db.models import User


async def create_test_user():
    """Create test user and return JWT token."""
    async with AsyncSessionLocal() as db:
        try:
            # Check if user already exists
            result = await db.execute(
                select(User).where(User.email == "testworkflow@example.com")
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                user_id = str(existing_user.user_id)
                print(f"User already exists: {user_id}")
            else:
                # Create new user
                user = User(
                    email="testworkflow@example.com",
                    username="testworkflow",
                    hashed_password=hash_password("testpass123"),
                    first_name="Test",
                    last_name="Workflow",
                    is_active=True,
                    is_verified=True,
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
                user_id = str(user.user_id)
                print(f"User created: {user_id}")

            # Generate JWT token (valid for 30 days)
            token = create_access_token(
                data={"sub": user_id},
                expires_delta=timedelta(days=30)
            )
            print(f"JWT Token: {token}")

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(create_test_user())
