
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from core.security import decode_access_token
from schemas.location_schema import (
    LocationCreate,
    LocationHistoryResponse,
    LocationResponse,
)
from services.device_service import get_user_devices
from services.location_service import (
    count_device_locations,
    get_latest_location,
    get_location_history,
    save_location,
)


router = APIRouter(
    prefix="/api/devices",
    tags=["Device Locations"],
)

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> int:
    """Authenticate the user through a JWT access token."""
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])

        if user_id <= 0:
            raise ValueError("Invalid user ID")

        return user_id

    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def ensure_device_owner(device_id: int, user_id: int) -> None:
    """Allow access only to devices registered to the current user."""
    devices = get_user_devices(user_id)

    for device in devices:
        # get_user_devices selects id as its first column.
        current_device_id = (
            device["id"] if isinstance(device, dict) else device[0]
        )

        if current_device_id == device_id:
            return

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Device not found.",
    )


@router.post("/{device_id}/location", status_code=status.HTTP_201_CREATED)
def upload_device_location(
    device_id: int,
    payload: LocationCreate,
    user_id: int = Depends(get_current_user),
):
    """Save a GPS location for an owned device."""
    ensure_device_owner(device_id, user_id)

    try:
        location_id = save_location(
            device_id=device_id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            accuracy_meters=payload.accuracy_meters,
            recorded_at=payload.recorded_at,
        )

        return {
            "message": "Location saved successfully.",
            "location_id": location_id,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        )


@router.get("/{device_id}/location/latest")
def read_latest_location(
    device_id: int,
    user_id: int = Depends(get_current_user),
):
    """Return the latest location for an owned device."""
    ensure_device_owner(device_id, user_id)

    location = get_latest_location(device_id)

    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No location has been recorded for this device.",
        )

    if not isinstance(location, dict):
        location = dict(zip(
            [
                "id",
                "device_id",
                "latitude",
                "longitude",
                "accuracy_meters",
                "recorded_at",
                "received_at",
            ],
            location,
        ))

    return location


@router.get(
    "/{device_id}/location/history",
    response_model=LocationHistoryResponse,
)
def read_location_history(
    device_id: int,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user_id: int = Depends(get_current_user),
):
    """Return paginated location history for an owned device."""
    ensure_device_owner(device_id, user_id)

    rows = get_location_history(
        device_id=device_id,
        limit=limit,
        offset=offset,
    )

    column_names = [
        "id",
        "device_id",
        "latitude",
        "longitude",
        "accuracy_meters",
        "recorded_at",
        "received_at",
    ]

    items = [
        row if isinstance(row, dict) else dict(zip(column_names, row))
        for row in rows
    ]

    total = count_device_locations(device_id)

    return LocationHistoryResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )
