
from database.connection import get_connection


def create_refresh_token(user_id, token_hash, expires_at):
    """Store a hashed refresh token for a user session."""

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                INSERT INTO refresh_tokens (
                    user_id,
                    token_hash,
                    expires_at
                )
                VALUES (%s, %s, %s)
            """

            cursor.execute(
                query,
                (user_id, token_hash, expires_at),
            )

            session_id = cursor.lastrowid

        connection.commit()
        return session_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_valid_refresh_token(token_hash):
    """Find a non-revoked, unexpired refresh token."""

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                SELECT
                    id,
                    user_id,
                    token_hash,
                    expires_at,
                    created_at
                FROM refresh_tokens
                WHERE token_hash = %s
                  AND revoked_at IS NULL
                  AND expires_at > UTC_TIMESTAMP()
                LIMIT 1
            """

            cursor.execute(query, (token_hash,))
            return cursor.fetchone()

    finally:
        connection.close()


def revoke_refresh_token(token_hash):
    """Revoke one refresh token during logout."""

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                UPDATE refresh_tokens
                SET revoked_at = UTC_TIMESTAMP()
                WHERE token_hash = %s
                  AND revoked_at IS NULL
            """

            cursor.execute(query, (token_hash,))
            revoked = cursor.rowcount > 0

        connection.commit()
        return revoked

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def revoke_user_sessions(user_id):
    """Revoke all active refresh tokens for a user."""

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                UPDATE refresh_tokens
                SET revoked_at = UTC_TIMESTAMP()
                WHERE user_id = %s
                  AND revoked_at IS NULL
            """

            cursor.execute(query, (user_id,))
            revoked_count = cursor.rowcount

        connection.commit()
        return revoked_count

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def delete_expired_tokens():
    """Delete expired refresh tokens during scheduled cleanup."""

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                DELETE FROM refresh_tokens
                WHERE expires_at < UTC_TIMESTAMP()
            """

            cursor.execute(query)
            deleted_count = cursor.rowcount

        connection.commit()
        return deleted_count

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
