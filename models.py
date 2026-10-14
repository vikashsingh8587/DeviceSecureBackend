
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LocationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device_id: str = Field(min_length=1, max_length=128)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    battery_level: int | None = Field(default=None, ge=0, le=100)
    timestamp: str = Field(min_length=1, max_length=64)


class CommandRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device_id: str = Field(min_length=1, max_length=128)
    command: Literal["TRIGGER_SIREN", "LOCK_DEVICE"]
    status: Literal["pending", "queued"] = "pending"


class LocationResponse(LocationUpdate):
    pass


class CommandResponse(BaseModel):
    command_id: str
    device_id: str
    command: str
    status: str


class CommandPollResponse(BaseModel):
    device_id: str
    commands: list[CommandResponse]
