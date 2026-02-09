"""Authentication router for user registration and login."""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from app.database import get_session
from app.models import User
from app.schemas import UserRegister, UserLogin, UserResponse
from app.auth import hash_password, verify_password, create_jwt

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    response: Response,
    session: Session = Depends(get_session)
):
    """Register a new user."""
    # Hash the password
    hashed_password = hash_password(user_data.password)

    # Create user
    user = User(
        email=user_data.email.lower(),  # Store email in lowercase
        hashed_password=hashed_password
    )

    try:
        session.add(user)
        session.commit()
        session.refresh(user)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Generate JWT token
    token = create_jwt(user.id)

    # Set HTTP-only cookie
    # For local development: no domain set (allows 127.0.0.1 and localhost to both work)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400,  # 24 hours
        path="/",       # Cookie valid for all paths
        # secure=True,  # Enable in production with HTTPS
    )

    return user


@router.post("/login", response_model=UserResponse)
async def login(
    credentials: UserLogin,
    response: Response,
    session: Session = Depends(get_session)
):
    """Login a user."""
    # Find user by email
    statement = select(User).where(User.email == credentials.email.lower())
    user = session.exec(statement).first()

    # Verify credentials (same error for wrong email or password - security)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Generate JWT token
    token = create_jwt(user.id)

    # Set HTTP-only cookie
    # For local development: no domain set (allows 127.0.0.1 and localhost to both work)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400,  # 24 hours
        path="/",       # Cookie valid for all paths
        # secure=True,  # Enable in production with HTTPS
    )

    return user


@router.post("/logout")
async def logout(response: Response):
    """Logout a user by clearing the JWT cookie."""
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax"
    )
    return {"message": "Successfully logged out"}
