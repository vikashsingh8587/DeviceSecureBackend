
import os
import pymysql
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Create MySQL connection
def get_connection():
    try:
            print("Connecting to MySQL database...")
            connection = pymysql.connect(
                host=os.getenv("DATABASE_HOST"),
                port=int(os.getenv("DATABASE_PORT", 3306)),
                user=os.getenv("DATABASE_USER"),
                password=os.getenv("DATABASE_PASSWORD"),
                database=os.getenv("DATABASE_NAME"),
                
                charset="utf8mb4"
            )
            return connection
    except pymysql.MySQLError as e:
        print("Error connecting to MySQL:", e)
        raise   


# Test database connection
if __name__ == "__main__":
    try:
        conn = get_connection()
        print("MySQL connected successfully!")

        conn.close()
        print("Connection closed.")

    except pymysql.MySQLError as error:
        print("MySQL connection failed:", error)
