
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LocationCreate(BaseModel):
    """GPS location sent by the mobile app."""

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy_meters: float | None = Field(
        default=None,
        ge=0,
        le=100_000,
    )
    recorded_at: datetime | None = None


class LocationResponse(BaseModel):
    """Location data returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    latitude: float
    longitude: float
    accuracy_meters: float | None = None
    recorded_at: datetime
    received_at: datetime | None = None


class LocationHistoryResponse(BaseModel):
    """Paginated location history."""

    items: list[LocationResponse]
    total: int
    limit: int
    offset: int
