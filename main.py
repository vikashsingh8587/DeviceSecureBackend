from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
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

# Existing API routers used by the React + Redux Toolkit dashboard.
from routers.auth_router import router as auth_router
from routers.devices_router import router as devices_router
from routers.device_status_router import router as device_status_router
from routers.locations_router import router as locations_router
from routers.security_events_router import router as security_events_router
from routers.commands_router import router as commands_router


app = FastAPI(
    title="OmniGuard API",
    description=(
        "Cloud API for the OmniGuard mobile app and web dashboard. "
        "Includes authentication, device management, locations, "
        "device status, security events, and commands."
    ),
    version="1.1.0",
)

# Allow the local Vite frontend and any explicitly configured deployment origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount existing routers; these use the project's existing services and MySQL layer.
app.include_router(auth_router)
app.include_router(devices_router)
app.include_router(device_status_router)
app.include_router(locations_router)
app.include_router(security_events_router)
app.include_router(commands_router)


# ---------------------------------------------------------------------------
# Legacy Flutter/mobile endpoints below are intentionally preserved.
# Their command queue is still in-memory; it is separate from /api/commands.
# ---------------------------------------------------------------------------
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
    """Legacy mobile endpoint: save location/telemetry to MySQL."""
    try:
        location_data = save_location_update(payload)

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
    """Legacy mobile endpoint: return the latest saved location."""
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
def queue_legacy_command(payload: CommandRequest):
    """Legacy mobile command endpoint; commands are held in process memory."""
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
def poll_legacy_commands(device_id: str):
    """Legacy mobile endpoint: poll and clear in-memory commands."""
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
