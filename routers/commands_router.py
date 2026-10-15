
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from core.security import decode_access_token
from schemas.command_schema import (
    CommandCancelResponse,
    CommandCreate,
    CommandResponse,
)
from services.command_service import (
    cancel_command,
    create_command,
    get_command,
    get_device_commands,
)


router = APIRouter(
    prefix="/api/commands",
    tags=["Device Commands"],
)

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> int:
    """Validate the JWT and return the authenticated user ID."""
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
    "",
    response_model=CommandResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_device_command(
    payload: CommandCreate,
    user_id: int = Depends(get_current_user),
):
    """Create a command for the user's active device."""
    try:
        command_id = create_command(
            device_id=payload.device_id,
            requested_by=user_id,
            command_type=payload.command_type,
            expires_at=payload.expires_at,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    command = get_command(command_id, user_id)

    if command is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Command created, but could not be retrieved.",
        )

    return command


@router.get("/device/{device_id}", response_model=list[CommandResponse])
def list_device_commands(
    device_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user_id: int = Depends(get_current_user),
):
    """List commands for a device owned by the user."""
    try:
        return get_device_commands(
            device_id=device_id,
            requested_by=user_id,
            limit=limit,
            offset=offset,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        )


@router.get("/{command_id}", response_model=CommandResponse)
def read_command(
    command_id: int,
    user_id: int = Depends(get_current_user),
):
    """Get a command only if it belongs to the user's device."""
    command = get_command(command_id, user_id)

    if command is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Command not found.",
        )

    return command


@router.delete("/{command_id}", response_model=CommandCancelResponse)
def cancel_device_command(
    command_id: int,
    user_id: int = Depends(get_current_user),
):
    """Cancel a pending command belonging to the user."""
    cancelled = cancel_command(command_id, user_id)

    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending command not found.",
        )

    return CommandCancelResponse(
        message="Command cancelled successfully.",
        command_id=command_id,
    )
