
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from core.config import settings
from core.security import decode_access_token
from schemas.device_schema import (
    DeviceRegister,
    DeviceResponse,
    DeviceUnlinkResponse,
    DeviceUpdate,
)
from services.device_service import (
    get_device_by_uuid,
    get_user_devices,
    register_device,
    unlink_device,
    update_device,
)


router = APIRouter(
    prefix="/api/devices",
    tags=["Devices"],
)

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    """Validate the JWT and return its user ID."""
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


@router.post(
    "/register",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_new_device(
    payload: DeviceRegister,
    user_id: int = Depends(get_current_user),
):
    print(f"Registering new device for user {user_id}: {payload.device_uuid} - {payload.device_name} this is call from router device")
    existing = get_device_by_uuid(payload.device_uuid)

    if existing:
        # Support either dictionary or tuple cursor results.
        existing_user_id = (
            existing["user_id"]
            if isinstance(existing, dict)
            else existing[1]
        )

        if existing_user_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This device is already registered.",
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This device cannot be registered.",
        )

    try:
        device_id = register_device(
            user_id=user_id,
            device_uuid=payload.device_uuid,
            device_name=payload.device_name,
            platform=payload.platform,
            model=payload.model,
            os_version=payload.os_version,
            app_version=payload.app_version,
        )
    except Exception:
        # Log the underlying error privately in production.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device registration failed. Check the device data.",
        )

    # Return the registered device using the existing service.
    devices = get_user_devices(user_id)
    for device in devices:
        device_data = (
            device if isinstance(device, dict)
            else dict(zip(
                [
                    "id", "user_id", "device_uuid", "device_name",
                    "platform", "model", "status",
                    "registered_at", "last_seen_at",
                ],
                device,
            ))
        )

        if device_data.get("id") == device_id:
            return device_data

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Device registered, but its details could not be loaded.",
    )


@router.get("", response_model=list[DeviceResponse])
def list_my_devices(
    user_id: int = Depends(get_current_user),
):
    return get_user_devices(user_id)


@router.put("/{device_id}", response_model=DeviceResponse)
def update_my_device(
    device_id: int,
    payload: DeviceUpdate,
    user_id: int = Depends(get_current_user),
):
    updated = update_device(
        device_id=device_id,
        user_id=user_id,
        device_name=payload.device_name,
        model=payload.model,
        os_version=payload.os_version,
        app_version=payload.app_version,
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found.",
        )

    # Load only the current user's devices.
    devices = get_user_devices(user_id)
    for device in devices:
        if isinstance(device, dict):
            if device.get("id") == device_id:
                return device

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Device not found.",
    )


@router.delete(
    "/{device_id}",
    response_model=DeviceUnlinkResponse,
)
def unlink_my_device(
    device_id: int,
    user_id: int = Depends(get_current_user),
):
    unlinked = unlink_device(device_id, user_id)

    if not unlinked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found or already unlinked.",
        )

    return DeviceUnlinkResponse(
        message="Device unlinked successfully.",
        device_id=device_id,
    )
