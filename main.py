
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status

from models import (
    LocationUpdate,
    LocationResponse,
    CommandRequest,
    CommandResponse,
    CommandPollResponse,
)

app = FastAPI(
    title="OmniGuard API",
    description=(
        "Cloud API for device location reporting "
        "and authorized remote security commands."
    ),
    version="1.0.0",
)

# In-memory storage. Data disappears when the process restarts.
locations: dict[str, LocationResponse] = {}
known_devices: set[str] = set()
command_queues: dict[str, list[CommandResponse]] = defaultdict(list)

# Protect shared in-memory state from concurrent requests.
state_lock = Lock()


@app.get("/")
def health_check():
    return {
        "service": "OmniGuard API",
        "status": "running",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post(
    "/api/device/location",
    response_model=LocationResponse,
    status_code=status.HTTP_200_OK,
)
def update_location(payload: LocationUpdate):
    """Receive and store a device's latest location and telemetry."""

    location = LocationResponse(**payload.model_dump())

    with state_lock:
        known_devices.add(payload.device_id)
        locations[payload.device_id] = location

    return location


@app.get(
    "/api/device/location/{device_id}",
    response_model=LocationResponse,
)
def get_location(device_id: str):
    """Return the latest known location of a device."""

    with state_lock:
        location = locations.get(device_id)

    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No location found for device '{device_id}'.",
        )

    return location


@app.post(
    "/api/device/command",
    response_model=CommandResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def queue_command(payload: CommandRequest):
    """Queue an authorized command for a registered device."""

    with state_lock:
        if payload.device_id not in known_devices:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Unknown device '{payload.device_id}'. "
                    "The device must report its location first."
                ),
            )

        command = CommandResponse(
            command_id=str(uuid4()),
            device_id=payload.device_id,
            command=payload.command,
            status="pending",
        )

        command_queues[payload.device_id].append(command)

    return command


@app.get(
    "/api/device/commands/{device_id}",
    response_model=CommandPollResponse,
)
def poll_commands(device_id: str):
    """Return pending commands and remove them from the queue."""

    with state_lock:
        if device_id not in known_devices:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unknown device '{device_id}'.",
            )

        # Fetch and clear atomically to prevent duplicate delivery
        # between concurrent polls in this process.
        pending = command_queues.pop(device_id, [])

    return CommandPollResponse(
        device_id=device_id,
        commands=pending,
    )
