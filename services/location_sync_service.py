
from datetime import datetime, timezone



from database.connection import get_connection


def _parse_timestamp(value: str) -> datetime:
    """Parse an ISO-8601 timestamp and normalize it to UTC."""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("timestamp must be a valid ISO-8601 value") from exc

    if parsed.tzinfo is None:
        # Treat timestamps without a timezone as UTC.
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc).replace(tzinfo=None)


def save_location_update(payload) -> dict:
    """
    Save a location update using the existing models.LocationUpdate model.

    payload fields:
    device_id, latitude, longitude, battery_level, timestamp
    """
    recorded_at = _parse_timestamp(payload.timestamp)
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            # The API's device_id is the device UUID, not numeric devices.id.
            cursor.execute(
                """
                SELECT id
                FROM devices
                WHERE device_uuid = %s
                  AND status = 'active'
                LIMIT 1
                """,
                (payload.device_id,),
            )
            row = cursor.fetchone()

            if row is None:
                raise LookupError("Device is not registered or is inactive.")

            device_pk = row["id"] if isinstance(row, dict) else row[0]

            # Preserve location history.
            cursor.execute(
                """
                INSERT INTO location_history (
                    device_id,
                    latitude,
                    longitude,
                    recorded_at
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    device_pk,
                    payload.latitude,
                    payload.longitude,
                    recorded_at,
                ),
            )

            # Create the status row if it doesn't exist, then update it.
            cursor.execute(
                """
                INSERT INTO device_status (
                    device_id,
                    battery_level,
                    is_online,
                    last_location_at
                )
                VALUES (%s, %s, TRUE, %s)
                ON DUPLICATE KEY UPDATE
                    battery_level = COALESCE(
                        VALUES(battery_level), battery_level
                    ),
                    is_online = TRUE,
                    last_location_at = VALUES(last_location_at)
                """,
                (
                    device_pk,
                    payload.battery_level,
                    recorded_at,
                ),
            )

            cursor.execute(
                """
                UPDATE devices
                SET last_seen_at = UTC_TIMESTAMP(3)
                WHERE id = %s
                """,
                (device_pk,),
            )

        connection.commit()

        # Return the same public fields expected by LocationResponse.
        return {
            "device_id": payload.device_id,
            "latitude": payload.latitude,
            "longitude": payload.longitude,
            "battery_level": payload.battery_level,
            "timestamp": payload.timestamp,
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


    
def get_latest_location_update(device_uuid: str) -> dict | None:
    """Fetch the latest saved location for a registered device."""
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM devices
                WHERE device_uuid = %s
                  AND status = 'active'
                LIMIT 1
                """,
                (device_uuid,),
            )
            row = cursor.fetchone()

            if row is None:
                return None

            device_pk = row["id"] if isinstance(row, dict) else row[0]

            cursor.execute(
                """
                SELECT latitude, longitude, recorded_at
                FROM location_history
                WHERE device_id = %s
                ORDER BY recorded_at DESC, id DESC
                LIMIT 1
                """,
                (device_pk,),
            )
            location = cursor.fetchone()

            if location is None:
                return None

            cursor.execute(
                """
                SELECT battery_level
                FROM device_status
                WHERE device_id = %s
                LIMIT 1
                """,
                (device_pk,),
            )
            status_row = cursor.fetchone()

            if isinstance(location, dict):
                latitude = location["latitude"]
                longitude = location["longitude"]
                timestamp = location["recorded_at"]
            else:
                latitude, longitude, timestamp = location

            if status_row is None:
                battery_level = None
            else:
                battery_level = (
                    status_row["battery_level"]
                    if isinstance(status_row, dict)
                    else status_row[0]
                )

            if isinstance(timestamp, datetime):
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)

                timestamp = timestamp.isoformat().replace("+00:00", "Z")

            return {
                "device_id": device_uuid,
                "latitude": float(latitude),
                "longitude": float(longitude),
                "battery_level": battery_level,
                "timestamp": timestamp,
            }

    finally:
        connection.close()
