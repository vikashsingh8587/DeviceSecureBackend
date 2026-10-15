
from database.connection import get_connection


def register_device(
    user_id,
    device_uuid,
    device_name,
    platform,
    model=None,
    os_version=None,
    app_version=None,
):
    """Register a device for an existing user."""
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                INSERT INTO devices (
                    user_id,
                    device_uuid,
                    device_name,
                    platform,
                    model,
                    os_version,
                    app_version
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            cursor.execute(
                query,
                (
                    user_id,
                    device_uuid,
                    device_name,
                    platform,
                    model,
                    os_version,
                    app_version,
                ),
            )

            device_id = cursor.lastrowid

        connection.commit()
        return device_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_device_by_uuid(device_uuid):
    """Find a device by its UUID."""
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                SELECT
                    id,
                    user_id,
                    device_uuid,
                    device_name,
                    platform,
                    model,
                    os_version,
                    app_version,
                    status,
                    registered_at,
                    last_seen_at
                FROM devices
                WHERE device_uuid = %s
                LIMIT 1
            """

            cursor.execute(query, (device_uuid,))
            return cursor.fetchone()

    finally:
        connection.close()


def get_user_devices(user_id):
    """Get all devices belonging to a user."""
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                SELECT
                    id,
                    user_id,
                    device_uuid,
                    device_name,
                    platform,
                    model,
                    os_version,
                    app_version,
                    status,
                    registered_at,
                    last_seen_at
                FROM devices
                WHERE user_id = %s
                ORDER BY registered_at DESC
            """

            cursor.execute(query, (user_id,))
            return cursor.fetchall()

    finally:
        connection.close()


def update_device(
    device_id,
    user_id,
    device_name,
    model=None,
    os_version=None,
    app_version=None,
):
    """Update a device only if it belongs to the given user."""
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                UPDATE devices
                SET
                    device_name = %s,
                    model = %s,
                    os_version = %s,
                    app_version = %s
                WHERE id = %s AND user_id = %s
            """

            cursor.execute(
                query,
                (
                    device_name,
                    model,
                    os_version,
                    app_version,
                    device_id,
                    user_id,
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


def mark_device_seen(device_id):
    """Update the last-seen timestamp when a device connects."""
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                UPDATE devices
                SET last_seen_at = UTC_TIMESTAMP(3)
                WHERE id = %s
            """

            cursor.execute(query, (device_id,))

        connection.commit()
        return True

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def unlink_device(device_id, user_id):
    """Unlink a device without deleting its history."""
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                UPDATE devices
                SET status = 'unlinked'
                WHERE id = %s AND user_id = %s
            """

            cursor.execute(query, (device_id, user_id))
            unlinked = cursor.rowcount > 0

        connection.commit()
        return unlinked

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
