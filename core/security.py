
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from dotenv import load_dotenv
from pwdlib import PasswordHash


# Load .env from the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash a password before storing it in MySQL."""
    if not password:
        raise ValueError("Password cannot be empty.")

    return password_hasher.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Check a password against its stored hash."""
    if not plain_password or not hashed_password:
        return False

    return password_hasher.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(
    user_id: int,
    email: str,
) -> str:
    """Create a signed JWT access token."""

    if not JWT_SECRET or JWT_SECRET == "REPLACE_WITH_A_LONG_RANDOM_SECRET":
        raise RuntimeError(
            "Set a strong JWT_SECRET in your .env file."
        )

    if JWT_EXPIRE_MINUTES <= 0:
        raise RuntimeError("JWT_EXPIRE_MINUTES must be positive.")

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    """Verify a JWT and return its claims."""

    if not JWT_SECRET or JWT_SECRET == "REPLACE_WITH_A_LONG_RANDOM_SECRET":
        raise RuntimeError(
            "Set a strong JWT_SECRET in your .env file."
        )

    return jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
        options={"require": ["sub", "exp", "iat"]},
    )
