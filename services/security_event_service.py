
import json

from database.connection import get_connection


ALLOWED_SEVERITIES = {"info", "warning", "critical"}


def create_security_event(
    device_id,
    event_type,
    severity="info",
    description=None,
    metadata=None,
):
    """Save a security event for an existing device."""

    if severity not in ALLOWED_SEVERITIES:
        raise ValueError("Invalid security event severity.")

    if not event_type or not event_type.strip():
        raise ValueError("Event type is required.")

    metadata_json = (
        json.dumps(metadata, ensure_ascii=False)
        if metadata is not None
        else None
    )

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                INSERT INTO security_events (
                    device_id,
                    event_type,
                    severity,
                    description,
                    metadata,
                    occurred_at
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    UTC_TIMESTAMP()
                )
            """

            cursor.execute(
                query,
                (
                    device_id,
                    event_type.strip(),
                    severity,
                    description,
                    metadata_json,
                ),
            )

            event_id = cursor.lastrowid

        connection.commit()
        return event_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_security_event(event_id, user_id):
    """Get an event only if its device belongs to the user."""

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                SELECT
                    e.id,
                    e.device_id,
                    e.event_type,
                    e.severity,
                    e.description,
                    e.metadata,
                    e.occurred_at,
                    e.created_at,
                    e.acknowledged_at
                FROM security_events AS e
                INNER JOIN devices AS d
                    ON d.id = e.device_id
                WHERE e.id = %s
                  AND d.user_id = %s
                LIMIT 1
            """

            cursor.execute(query, (event_id, user_id))
            return cursor.fetchone()

    finally:
        connection.close()


def get_device_security_events(
    device_id,
    user_id,
    limit=50,
    offset=0,
):
    """Get security events for a device owned by the user."""

    if not 1 <= limit <= 200:
        raise ValueError("Limit must be between 1 and 200.")

    if offset < 0:
        raise ValueError("Offset cannot be negative.")

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                SELECT
                    e.id,
                    e.device_id,
                    e.event_type,
                    e.severity,
                    e.description,
                    e.metadata,
                    e.occurred_at,
                    e.created_at,
                    e.acknowledged_at
                FROM security_events AS e
                INNER JOIN devices AS d
                    ON d.id = e.device_id
                WHERE e.device_id = %s
                  AND d.user_id = %s
                ORDER BY e.occurred_at DESC, e.id DESC
                LIMIT %s OFFSET %s
            """

            cursor.execute(
                query,
                (device_id, user_id, limit, offset),
            )

            return cursor.fetchall()

    finally:
        connection.close()


def get_unacknowledged_events(device_id, user_id):
    """Get unacknowledged events for the user's device."""

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                SELECT
                    e.id,
                    e.device_id,
                    e.event_type,
                    e.severity,
                    e.description,
                    e.occurred_at
                FROM security_events AS e
                INNER JOIN devices AS d
                    ON d.id = e.device_id
                WHERE e.device_id = %s
                  AND d.user_id = %s
                  AND e.acknowledged_at IS NULL
                ORDER BY e.occurred_at DESC, e.id DESC
            """

            cursor.execute(query, (device_id, user_id))
            return cursor.fetchall()

    finally:
        connection.close()


def acknowledge_security_event(event_id, user_id):
    """Acknowledge an event belonging to the user's device."""

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                UPDATE security_events AS e
                INNER JOIN devices AS d
                    ON d.id = e.device_id
                SET e.acknowledged_at = UTC_TIMESTAMP()
                WHERE e.id = %s
                  AND d.user_id = %s
                  AND e.acknowledged_at IS NULL
            """

            cursor.execute(query, (event_id, user_id))
            acknowledged = cursor.rowcount > 0

        connection.commit()
        return acknowledged

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
