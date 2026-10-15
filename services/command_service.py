
from database.connection import get_connection


ALLOWED_COMMANDS = {"ring", "lock", "locate", "sync"}

ALLOWED_STATUSES = {
    "pending",
    "sent",
    "acknowledged",
    "completed",
    "failed",
    "expired",
    "cancelled",
}


def create_command(
    device_id,
    requested_by,
    command_type,
    expires_at,
):
    """Create a command for a device owned by the requesting user."""

    if command_type not in ALLOWED_COMMANDS:
        raise ValueError("Unsupported command type.")

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            # Verify device ownership before creating a command.
            ownership_query = """
                SELECT id
                FROM devices
                WHERE id = %s
                  AND user_id = %s
                  AND status = 'active'
                LIMIT 1
            """

            cursor.execute(
                ownership_query,
                (device_id, requested_by),
            )

            if cursor.fetchone() is None:
                raise ValueError(
                    "Device not found or not available to this user."
                )

            query = """
                INSERT INTO device_commands (
                    device_id,
                    requested_by,
                    command_type,
                    expires_at
                )
                VALUES (%s, %s, %s, %s)
            """

            cursor.execute(
                query,
                (
                    device_id,
                    requested_by,
                    command_type,
                    expires_at,
                ),
            )

            command_id = cursor.lastrowid

        connection.commit()
        return command_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_command(command_id, requested_by):
    """Get a command only if it belongs to the requesting user."""

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                SELECT
                    c.id,
                    c.device_id,
                    c.requested_by,
                    c.command_type,
                    c.status,
                    c.requested_at,
                    c.expires_at,
                    c.completed_at,
                    c.result_message
                FROM device_commands AS c
                INNER JOIN devices AS d
                    ON d.id = c.device_id
                WHERE c.id = %s
                  AND d.user_id = %s
                LIMIT 1
            """

            cursor.execute(query, (command_id, requested_by))
            return cursor.fetchone()

    finally:
        connection.close()


def get_device_commands(
    device_id,
    requested_by,
    limit=50,
    offset=0,
):
    """List commands for a device owned by the requesting user."""

    if not 1 <= limit <= 200:
        raise ValueError("Limit must be between 1 and 200.")

    if offset < 0:
        raise ValueError("Offset cannot be negative.")

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                SELECT
                    c.id,
                    c.device_id,
                    c.command_type,
                    c.status,
                    c.requested_at,
                    c.expires_at,
                    c.completed_at,
                    c.result_message
                FROM device_commands AS c
                INNER JOIN devices AS d
                    ON d.id = c.device_id
                WHERE c.device_id = %s
                  AND d.user_id = %s
                ORDER BY c.requested_at DESC
                LIMIT %s OFFSET %s
            """

            cursor.execute(
                query,
                (device_id, requested_by, limit, offset),
            )

            return cursor.fetchall()

    finally:
        connection.close()


def update_command_status(
    command_id,
    new_status,
    result_message=None,
):
    """Update command status when called by a trusted backend worker."""

    if new_status not in ALLOWED_STATUSES:
        raise ValueError("Invalid command status.")

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                UPDATE device_commands
                SET
                    status = %s,
                    result_message = %s,
                    completed_at = CASE
                        WHEN %s IN (
                            'completed', 'failed', 'expired', 'cancelled'
                        )
                        THEN UTC_TIMESTAMP()
                        ELSE completed_at
                    END
                WHERE id = %s
                  AND status IN ('pending', 'sent', 'acknowledged')
            """

            cursor.execute(
                query,
                (
                    new_status,
                    result_message,
                    new_status,
                    command_id,
                ),
            )

            updated = cursor.rowcount > 0

        connection.commit()
        return updated

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def cancel_command(command_id, requested_by):
    """Cancel a pending command belonging to the user's device."""

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                UPDATE device_commands AS c
                INNER JOIN devices AS d
                    ON d.id = c.device_id
                SET
                    c.status = 'cancelled',
                    c.completed_at = UTC_TIMESTAMP()
                WHERE c.id = %s
                  AND d.user_id = %s
                  AND c.status = 'pending'
            """

            cursor.execute(query, (command_id, requested_by))
            cancelled = cursor.rowcount > 0

        connection.commit()
        return cancelled

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
