
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from core.security import decode_access_token
from schemas.device_status_schema import (
    DeviceStatusResponse,
    DeviceStatusUpdate,
)
from services.device_service import get_user_devices
from services.device_status_service import (
    get_device_status,
    update_device_status,
)


router = APIRouter(
    prefix="/api/devices",
    tags=["Device Status"],
)

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> int:
    """Validate the access token and return the user ID."""
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
    """Verify that the device belongs to the authenticated user."""
    devices = get_user_devices(user_id)

    for device in devices:
        current_device_id = (
            device["id"] if isinstance(device, dict) else device[0]
        )

        if current_device_id == device_id:
            return

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Device not found.",
    )


@router.get(
    "/{device_id}/status",
    response_model=DeviceStatusResponse,
)
def read_device_status(
    device_id: int,
    user_id: int = Depends(get_current_user),
):
    """Get status for a device owned by the user."""
    ensure_device_owner(device_id, user_id)

    device_status = get_device_status(device_id)

    if device_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device status has not been reported yet.",
        )

    return device_status


@router.put(
    "/{device_id}/status",
    status_code=status.HTTP_200_OK,
)
def update_status_from_device(
    device_id: int,
    payload: DeviceStatusUpdate,
    user_id: int = Depends(get_current_user),
):
    """Update status for an owned device."""
    ensure_device_owner(device_id, user_id)

    try:
        update_device_status(
            device_id=device_id,
            battery_level=payload.battery_level,
            is_charging=payload.is_charging,
            is_online=payload.is_online,
            location_permission=payload.location_permission,
            gps_enabled=payload.gps_enabled,
        )

        return {"message": "Device status updated successfully."}

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        )

