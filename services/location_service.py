
from datetime import datetime, timezone

from database.connection import get_connection


def save_location(
    device_id,
    latitude,
    longitude,
    accuracy_meters=None,
    recorded_at=None,
):
    """Save a device location in the database."""

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90.")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180.")

    if accuracy_meters is not None and accuracy_meters < 0:
        raise ValueError("Accuracy cannot be negative.")

    if recorded_at is None:
        recorded_at = datetime.now(timezone.utc).replace(tzinfo=None)

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                INSERT INTO location_history (
                    device_id,
                    latitude,
                    longitude,
                    accuracy_meters,
                    recorded_at
                )
                VALUES (%s, %s, %s, %s, %s)
            """

            cursor.execute(
                query,
                (
                    device_id,
                    latitude,
                    longitude,
                    accuracy_meters,
                    recorded_at,
                ),
            )

            location_id = cursor.lastrowid

            # Update the device's latest-location timestamp.
            status_query = """
                UPDATE device_status
                SET last_location_at = %s
                WHERE device_id = %s
            """

            cursor.execute(status_query, (recorded_at, device_id))

        connection.commit()
        return location_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_latest_location(device_id):
    """Return the latest recorded location of a device."""
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                SELECT
                    id,
                    device_id,
                    latitude,
                    longitude,
                    accuracy_meters,
                    recorded_at,
                    received_at
                FROM location_history
                WHERE device_id = %s
                ORDER BY recorded_at DESC, id DESC
                LIMIT 1
            """

            cursor.execute(query, (device_id,))
            return cursor.fetchone()

    finally:
        connection.close()


def get_location_history(device_id, limit=50, offset=0):
    """Return paginated location history."""
    if not 1 <= limit <= 500:
        raise ValueError("Limit must be between 1 and 500.")

    if offset < 0:
        raise ValueError("Offset cannot be negative.")

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                SELECT
                    id,
                    device_id,
                    latitude,
                    longitude,
                    accuracy_meters,
                    recorded_at,
                    received_at
                FROM location_history
                WHERE device_id = %s
                ORDER BY recorded_at DESC, id DESC
                LIMIT %s OFFSET %s
            """

            cursor.execute(query, (device_id, limit, offset))
            return cursor.fetchall()

    finally:
        connection.close()


def count_device_locations(device_id):
    """Count stored location records for a device."""
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                SELECT COUNT(*) AS total_locations
                FROM location_history
                WHERE device_id = %s
            """

            cursor.execute(query, (device_id,))
            result = cursor.fetchone()

            return result["total_locations"]

    finally:
        connection.close()
