
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


CommandType = Literal["ring", "lock", "locate", "sync"]

CommandStatus = Literal[
    "pending",
    "sent",
    "acknowledged",
    "completed",
    "failed",
    "expired",
    "cancelled",
]


class CommandCreate(BaseModel):
    """Request to create a command for an authorized device."""

    device_id: int = Field(gt=0)
    command_type: CommandType
    expires_at: datetime


class CommandStatusUpdate(BaseModel):
    """Status reported by an authorized device or backend worker."""

    status: Literal[
        "sent",
        "acknowledged",
        "completed",
        "failed",
    ]
    result_message: str | None = Field(
        default=None,
        max_length=500,
    )


class CommandResponse(BaseModel):
    """Command details returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    requested_by: int
    command_type: str
    status: str
    requested_at: datetime
    expires_at: datetime
    completed_at: datetime | None = None
    result_message: str | None = None


class CommandCancelResponse(BaseModel):
    """Response after attempting to cancel a command."""

    message: str
    command_id: int
