
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

from services.location_sync_service import (
    save_location_update,
    get_latest_location_update,
)


app = FastAPI(
    title="OmniGuard API",
    description=(
        "Cloud API for device location reporting "
        "and authorized remote security commands."
    ),
    version="1.0.0",
)


# Temporary in-memory storage for commands.
# Command persistence will be moved to MySQL separately.
known_devices: set[str] = set()
command_queues: dict[str, list[CommandResponse]] = defaultdict(list)

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
    """Save a device location and telemetry to MySQL."""

    try:
        location_data = save_location_update(payload)

        # Keep legacy command functionality working in this process.
        with state_lock:
            known_devices.add(payload.device_id)

        return LocationResponse(**location_data)

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@app.get(
    "/api/device/location/{device_id}",
    response_model=LocationResponse,
)
def get_location(device_id: str):
    """Return the latest saved location from MySQL."""

    try:
        location_data = get_latest_location_update(device_id)

    except Exception as exc:
        # Keep database details out of the API response.
        print(f"Location database error: {exc}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to fetch location from the database.",
        ) from exc

    if location_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No location found for device '{device_id}'.",
        )

    return LocationResponse(**location_data)


@app.post(
    "/api/device/command",
    response_model=CommandResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def queue_command(payload: CommandRequest):
    """Queue a command for a device known to this server process."""

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
    """Return pending commands and clear the in-memory queue."""

    with state_lock:
        if device_id not in known_devices:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unknown device '{device_id}'.",
            )

        pending = command_queues.pop(device_id, [])

    return CommandPollResponse(
        device_id=device_id,
        commands=pending,
    )
