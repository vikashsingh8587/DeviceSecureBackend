
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from core.security import decode_access_token
from schemas.security_event_schema import (
    SecurityEventAcknowledgeResponse,
    SecurityEventCreate,
    SecurityEventListResponse,
    SecurityEventResponse,
)
from services.device_service import get_user_devices
from services.security_event_service import (
    acknowledge_security_event,
    create_security_event,
    get_device_security_events,
    get_security_event,
    get_unacknowledged_events,
)


router = APIRouter(
    prefix="/api/devices",
    tags=["Security Events"],
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
    """Check that the device belongs to the authenticated user."""
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


@router.post(
    "/{device_id}/security-events",
    status_code=status.HTTP_201_CREATED,
)
def report_security_event(
    device_id: int,
    payload: SecurityEventCreate,
    user_id: int = Depends(get_current_user),
):
    """Record an event after verifying device ownership."""
    ensure_device_owner(device_id, user_id)

    event_id = create_security_event(
        device_id=device_id,
        event_type=payload.event_type,
        severity=payload.severity,
        description=payload.description,
        metadata=payload.metadata,
    )

    return {
        "message": "Security event recorded.",
        "event_id": event_id,
    }


@router.get(
    "/{device_id}/security-events",
    response_model=SecurityEventListResponse,
)
def list_security_events(
    device_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user_id: int = Depends(get_current_user),
):
    """List security events for the user's device."""
    ensure_device_owner(device_id, user_id)

    rows = get_device_security_events(
        device_id=device_id,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )

    return SecurityEventListResponse(
        items=rows,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{device_id}/security-events/unacknowledged",
    response_model=list[SecurityEventResponse],
)
def list_unacknowledged_events(
    device_id: int,
    user_id: int = Depends(get_current_user),
):
    """List events that have not yet been acknowledged."""
    ensure_device_owner(device_id, user_id)

    return get_unacknowledged_events(device_id, user_id)


@router.get(
    "/security-events/{event_id}",
    response_model=SecurityEventResponse,
)
def read_security_event(
    event_id: int,
    user_id: int = Depends(get_current_user),
):
    """Get an event only if it belongs to the user's device."""
    event = get_security_event(event_id, user_id)

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security event not found.",
        )

    return event


@router.post(
    "/security-events/{event_id}/acknowledge",
    response_model=SecurityEventAcknowledgeResponse,
)
def acknowledge_event(
    event_id: int,
    user_id: int = Depends(get_current_user),
):
    """Acknowledge an event belonging to the user's device."""
    acknowledged = acknowledge_security_event(event_id, user_id)

    if not acknowledged:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unacknowledged event not found.",
        )

    return SecurityEventAcknowledgeResponse(
        message="Security event acknowledged.",
        event_id=event_id,
    )
