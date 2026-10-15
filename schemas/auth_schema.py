
from pydantic import BaseModel, Field

from schemas.user_schema import UserResponse


class TokenResponse(BaseModel):
    """JWT token returned after successful authentication."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(gt=0)


class LoginResponse(BaseModel):
    """Successful login response."""

    message: str
    token: TokenResponse
    user: UserResponse


class RegisterResponse(BaseModel):
    """Successful registration response."""

    message: str
    user: UserResponse


class LogoutResponse(BaseModel):
    """Successful logout response."""

    message: str
