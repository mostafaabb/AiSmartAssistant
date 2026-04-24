"""
Authentication routes for NexusAI API.
Handles user registration, login, and token refresh.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
import logging

from backend.app.core import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_db,
    settings,
)
from backend.app.models import User
from backend.app.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account.

    Validates email uniqueness and creates a new user with hashed password.
    Returns JWT access and refresh tokens on success.

    Args:
        request: User registration data (email, username, password, optional name)
        db: Database session

    Returns:
        TokenResponse with access_token, refresh_token, and token_type

    Raises:
        HTTPException 400: Email or username already exists
        HTTPException 422: Invalid input data
    """
    try:
        # Check if email already exists
        result = await db.execute(
            select(User).where(User.email == request.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Check if username already exists
        result = await db.execute(
            select(User).where(User.username == request.username)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

        # Create new user
        new_user = User(
            email=request.email,
            username=request.username,
            password_hash=hash_password(request.password),
            first_name=request.first_name,
            last_name=request.last_name,
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        logger.info(f"✅ New user registered: {new_user.email}")

        # Generate tokens
        access_token = create_access_token({"sub": str(new_user.id)})
        refresh_token = create_refresh_token({"sub": str(new_user.id)})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    User login with email and password.

    Validates credentials and returns JWT tokens.

    Args:
        request: Login credentials (email, password)
        db: Database session

    Returns:
        TokenResponse with access_token and refresh_token

    Raises:
        HTTPException 401: Invalid credentials
    """
    try:
        # Find user by email
        result = await db.execute(
            select(User).where(User.email == request.email)
        )
        user = result.scalar_one_or_none()

        # Validate credentials
        if not user or not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )

        # Update last login
        from datetime import datetime
        user.last_login = datetime.utcnow()
        await db.commit()

        logger.info(f"✅ User logged in: {user.email}")

        # Generate tokens
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: dict, db: AsyncSession = Depends(get_db)):
    """
    Refresh access token using refresh token.

    Args:
        request: Dictionary with 'refresh_token' key
        db: Database session

    Returns:
        TokenResponse with new access_token

    Raises:
        HTTPException 401: Invalid or expired refresh token
    """
    try:
        refresh_token_str = request.get("refresh_token")
        if not refresh_token_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="refresh_token required"
            )

        # Verify refresh token
        payload = verify_token(refresh_token_str)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        user_id = payload.get("sub")

        # Verify user still exists and is active
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Generate new access token
        access_token = create_access_token({"sub": str(user.id)})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to refresh token"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user_id: str = Depends(lambda: None),  # Placeholder
    db: AsyncSession = Depends(get_db)
):
    """
    Get current authenticated user's profile information.

    Args:
        current_user_id: User ID from JWT token (injected by auth middleware)
        db: Database session

    Returns:
        UserResponse with user information

    Raises:
        HTTPException 404: User not found
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    result = await db.execute(
        select(User).where(User.id == current_user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse.from_orm(user)


@router.post("/logout")
async def logout():
    """
    User logout endpoint.

    Since JWT tokens are stateless, this just returns success.
    The frontend should discard the tokens.

    Returns:
        Success message
    """
    return {"message": "Successfully logged out. Please discard your tokens."}
