
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DeviceRegister(BaseModel):
    """Data required to register a mobile device."""

    device_uuid: str = Field(min_length=8, max_length=128)
    device_name: str = Field(min_length=1, max_length=100)
    platform: Literal["android", "ios", "windows", "macos", "linux"]
    model: str | None = Field(default=None, max_length=100)
    os_version: str | None = Field(default=None, max_length=50)
    app_version: str | None = Field(default=None, max_length=50)


class DeviceUpdate(BaseModel):
    """Fields that can be updated for a registered device."""

    device_name: str = Field(min_length=1, max_length=100)
    model: str | None = Field(default=None, max_length=100)
    os_version: str | None = Field(default=None, max_length=50)
    app_version: str | None = Field(default=None, max_length=50)


class DeviceResponse(BaseModel):
    """Device information returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    device_uuid: str
    device_name: str
    platform: str
    model: str | None = None
    os_version: str | None = None
    app_version: str | None = None
    status: str
    registered_at: datetime | None = None
    last_seen_at: datetime | None = None


class DeviceUnlinkResponse(BaseModel):
    """Response after unlinking a device."""

    message: str
    device_id: int
