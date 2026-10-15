
import json

from database.connection import get_connection


def create_audit_log(
    action,
    user_id=None,
    device_id=None,
    details=None,
    ip_address=None,
):
    """Record an important action in the audit log."""

    details_json = (
        json.dumps(details, ensure_ascii=False)
        if details is not None
        else None
    )

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                INSERT INTO audit_logs (
                    user_id,
                    device_id,
                    action,
                    details,
                    ip_address
                )
                VALUES (%s, %s, %s, %s, %s)
            """

            cursor.execute(
                query,
                (
                    user_id,
                    device_id,
                    action,
                    details_json,
                    ip_address,
                ),
            )

            log_id = cursor.lastrowid

        connection.commit()
        return log_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_audit_log(log_id):
    """Retrieve one audit log entry."""

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                SELECT
                    id,
                    user_id,
                    device_id,
                    action,
                    details,
                    ip_address,
                    created_at
                FROM audit_logs
                WHERE id = %s
                LIMIT 1
            """

            cursor.execute(query, (log_id,))
            return cursor.fetchone()

    finally:
        connection.close()


def get_user_audit_logs(user_id, limit=50, offset=0):
    """Retrieve audit history for a user."""

    if not 1 <= limit <= 200:
        raise ValueError("Limit must be between 1 and 200.")

    if offset < 0:
        raise ValueError("Offset cannot be negative.")

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                SELECT
                    id,
                    user_id,
                    device_id,
                    action,
                    details,
                    ip_address,
                    created_at
                FROM audit_logs
                WHERE user_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT %s OFFSET %s
            """

            cursor.execute(
                query,
                (user_id, limit, offset),
            )

            return cursor.fetchall()

    finally:
        connection.close()


def get_device_audit_logs(
    device_id,
    user_id,
    limit=50,
    offset=0,
):
    """Retrieve logs for a device owned by the requesting user."""

    if not 1 <= limit <= 200:
        raise ValueError("Limit must be between 1 and 200.")

    if offset < 0:
        raise ValueError("Offset cannot be negative.")

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                SELECT
                    a.id,
                    a.user_id,
                    a.device_id,
                    a.action,
                    a.details,
                    a.ip_address,
                    a.created_at
                FROM audit_logs AS a
                INNER JOIN devices AS d
                    ON d.id = a.device_id
                WHERE a.device_id = %s
                  AND d.user_id = %s
                ORDER BY a.created_at DESC, a.id DESC
                LIMIT %s OFFSET %s
            """

            cursor.execute(
                query,
                (device_id, user_id, limit, offset),
            )

            return cursor.fetchall()

    finally:
        connection.close()


def get_all_audit_logs(limit=50, offset=0):
    """Retrieve audit logs for authorized administrators only."""

    if not 1 <= limit <= 200:
        raise ValueError("Limit must be between 1 and 200.")

    if offset < 0:
        raise ValueError("Offset cannot be negative.")

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                SELECT
                    id,
                    user_id,
                    device_id,
                    action,
                    details,
                    ip_address,
                    created_at
                FROM audit_logs
                ORDER BY created_at DESC, id DESC
                LIMIT %s OFFSET %s
            """

            cursor.execute(query, (limit, offset))
            return cursor.fetchall()

    finally:
        connection.close()
