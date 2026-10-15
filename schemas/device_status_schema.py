
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DeviceStatusUpdate(BaseModel):
    """Device status reported by the Flutter app."""

    battery_level: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    is_charging: bool | None = None
    is_online: bool = True
    location_permission: bool | None = None
    gps_enabled: bool | None = None


class DeviceStatusResponse(BaseModel):
    """Device status returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    device_id: int
    battery_level: int | None = None
    is_charging: bool | None = None
    is_online: bool
    location_permission: bool | None = None
    gps_enabled: bool | None = None
    last_location_at: datetime | None = None
    updated_at: datetime | None = None
