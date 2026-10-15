from database.connection import get_connection


def create_user(full_name, email, password_hash):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                INSERT INTO users
                    (full_name, email, password_hash)
                VALUES (%s, %s, %s)
            """

            cursor.execute(
                query,
                (full_name, email, password_hash)
            )

            user_id = cursor.lastrowid

        connection.commit()
        return user_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_user_by_email(email):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                SELECT id, full_name, email, password_hash, is_active
                FROM users
                WHERE email = %s
                LIMIT 1
            """

            cursor.execute(query, (email,))
            return cursor.fetchone()

    finally:
        connection.close()


def update_user(user_id, full_name):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                UPDATE users
                SET full_name = %s
                WHERE id = %s
            """

            cursor.execute(query, (full_name, user_id))

        connection.commit()
        return True

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def delete_user(user_id):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            query = """
                DELETE FROM users
                WHERE id = %s
            """

            cursor.execute(query, (user_id,))
            deleted = cursor.rowcount > 0

        connection.commit()
        return deleted

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()