
from fastapi import APIRouter, HTTPException, status
import pymysql

from core.config import settings
from core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from schemas.auth_schema import (
    LoginResponse,
    RegisterResponse,
    TokenResponse,
)
from schemas.user_schema import UserCreate, UserLogin, UserResponse
from services.user_service import create_user, get_user_by_email


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


def _user_row_to_dict(row):
    """Support both dictionary and tuple database rows."""
    if row is None or isinstance(row, dict):
        return row

    # Column order returned by get_user_by_email().
    columns = [
        "id",
        "full_name",
        "email",
        "password_hash",
        "is_active",
        "created_at",
    ]
    return dict(zip(columns, row))


def _safe_user(row):
    """Remove password_hash before returning user data."""
    user = _user_row_to_dict(row)

    if user is None:
        return None

    return UserResponse(
        id=user["id"],
        full_name=user["full_name"],
        email=user["email"],
        is_active=bool(user["is_active"]),
        created_at=user.get("created_at"),
    )


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(payload: UserCreate):
    existing_user = get_user_by_email(str(payload.email))

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    password_hash = hash_password(payload.password)

    try:
        create_user(
            full_name=payload.full_name,
            email=str(payload.email),
            password_hash=password_hash,
        )
    except pymysql.err.IntegrityError:
        # Also handle simultaneous registration attempts.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user_row = get_user_by_email(str(payload.email))

    if not user_row:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Account created, but user details could not be loaded.",
        )

    return RegisterResponse(
        message="Registration successful.",
        user=_safe_user(user_row),
    )


@router.post("/login", response_model=LoginResponse)
def login_user(payload: UserLogin):
    user_row = get_user_by_email(str(payload.email))
    user = _user_row_to_dict(user_row)

    # Use a generic message to avoid revealing whether an email exists.
    if (
        not user
        or not verify_password(
            payload.password,
            user["password_hash"],
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not bool(user["is_active"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive.",
        )

    access_token = create_access_token(
        user_id=user["id"],
        email=user["email"],
    )

    return LoginResponse(
        message="Login successful.",
        token=TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRE_MINUTES * 60,
        ),
        user=_safe_user(user),
    )
