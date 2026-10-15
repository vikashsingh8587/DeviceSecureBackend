
from database.connection import get_connection


def get_device_status(device_id):
    """Get the current status of a device."""
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                SELECT
                    device_id,
                    battery_level,
                    is_charging,
                    is_online,
                    location_permission,
                    gps_enabled,
                    last_location_at,
                    updated_at
                FROM device_status
                WHERE device_id = %s
                LIMIT 1
            """

            cursor.execute(query, (device_id,))
            return cursor.fetchone()

    finally:
        connection.close()


def update_device_status(
    device_id,
    battery_level=None,
    is_charging=None,
    is_online=True,
    location_permission=None,
    gps_enabled=None,
):
    """Insert or update the status reported by a device."""

    if battery_level is not None and not 0 <= battery_level <= 100:
        raise ValueError("Battery level must be between 0 and 100.")

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                INSERT INTO device_status (
                    device_id,
                    battery_level,
                    is_charging,
                    is_online,
                    location_permission,
                    gps_enabled
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    battery_level = COALESCE(
                        VALUES(battery_level), battery_level
                    ),
                    is_charging = COALESCE(
                        VALUES(is_charging), is_charging
                    ),
                    is_online = VALUES(is_online),
                    location_permission = COALESCE(
                        VALUES(location_permission),
                        location_permission
                    ),
                    gps_enabled = COALESCE(
                        VALUES(gps_enabled), gps_enabled
                    )
            """

            cursor.execute(
                query,
                (
                    device_id,
                    battery_level,
                    is_charging,
                    is_online,
                    location_permission,
                    gps_enabled,
                ),
            )

        connection.commit()
        return True

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def mark_device_offline(device_id):
    """Mark a device as offline."""
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                UPDATE device_status
                SET is_online = FALSE
                WHERE device_id = %s
            """

            cursor.execute(query, (device_id,))
            updated = cursor.rowcount > 0

        connection.commit()
        return updated

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def update_location_settings(
    device_id,
    gps_enabled,
    location_permission,
):
    """Update GPS and location permission status."""
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                UPDATE device_status
                SET
                    gps_enabled = %s,
                    location_permission = %s
                WHERE device_id = %s
            """

            cursor.execute(
                query,
                (gps_enabled, location_permission, device_id),
            )
            updated = cursor.rowcount > 0

        connection.commit()
        return updated

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
