
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Data required to register a new user."""

    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    """Data required for login."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    """Fields a user can update in their profile."""

    full_name: str = Field(min_length=2, max_length=100)


class UserResponse(BaseModel):
    """Safe user data returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    is_active: bool
    created_at: datetime | None = None


class MessageResponse(BaseModel):
    """Standard API message."""

    message: str
