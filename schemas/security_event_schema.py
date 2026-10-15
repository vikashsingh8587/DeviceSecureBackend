
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


Severity = Literal["info", "warning", "critical"]


class SecurityEventCreate(BaseModel):
    """Security event reported by an authenticated device."""

    event_type: str = Field(min_length=1, max_length=100)
    severity: Severity = "info"
    description: str | None = Field(
        default=None,
        max_length=1000,
    )
    metadata: dict[str, Any] | None = None


class SecurityEventResponse(BaseModel):
    """Security event returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    event_type: str
    severity: Severity
    description: str | None = None
    metadata: dict[str, Any] | None = None
    occurred_at: datetime
    created_at: datetime | None = None
    acknowledged_at: datetime | None = None


class SecurityEventListResponse(BaseModel):
    """Paginated security event list."""

    items: list[SecurityEventResponse]
    limit: int
    offset: int


class SecurityEventAcknowledgeResponse(BaseModel):
    """Response after acknowledging an event."""

    message: str
    event_id: int
