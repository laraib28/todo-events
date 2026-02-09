"""FastAPI dependencies for authentication and database."""

import os
from fastapi import Depends, HTTPException, status, Cookie
from sqlmodel import Session
from typing import Optional
from app.database import get_session
from app.auth import decode_jwt
from app.models import User


async def get_current_user(
    access_token: Optional[str] = Cookie(None),
    session: Session = Depends(get_session)
) -> User:
    """Get the current authenticated user from JWT cookie."""
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    payload = decode_jwt(access_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user


# ============================================================================
# DEV-ONLY AUTHENTICATION BYPASS - DO NOT USE IN PRODUCTION
# ============================================================================
async def get_dev_or_current_user(
    access_token: Optional[str] = Cookie(None),
    session: Session = Depends(get_session)
) -> User:
    """
    DEV-ONLY: Get dev user for local testing OR authenticated user in production.

    ⚠️  WARNING: THIS IS FOR LOCAL DEVELOPMENT ONLY ⚠️

    Behavior:
    - ENVIRONMENT=development → Returns fixed dev user (id=1) for curl testing
    - ENVIRONMENT=production → Full JWT authentication required

    This allows testing /api/chat with curl without JWT tokens locally.
    Production behavior is UNCHANGED - full authentication required.

    DO NOT USE THIS IN PRODUCTION ENDPOINTS.
    """
    environment = os.getenv("ENVIRONMENT", "production").lower()

    # DEV MODE: Return fixed dev user for easy curl testing
    if environment == "development":
        # Try to get dev user (id=1)
        dev_user = session.get(User, 1)

        if not dev_user:
            # Dev user doesn't exist - create it
            from app.auth import hash_password
            dev_user = User(
                email="dev@local.test",
                hashed_password=hash_password("dev123"),
                name="DEV USER (Local Testing Only)"
            )
            session.add(dev_user)
            session.commit()
            session.refresh(dev_user)

        return dev_user

    # PRODUCTION MODE: Full authentication required (same as get_current_user)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    payload = decode_jwt(access_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user
# ============================================================================
