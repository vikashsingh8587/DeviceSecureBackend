
import os
from pathlib import Path

from dotenv import load_dotenv


# Load .env from the project root directory.
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


class Settings:
    """Central configuration for OmniGuard."""

    APP_NAME = os.getenv("APP_NAME", "OmniGuard API")
    APP_ENV = os.getenv("APP_ENV", "development")

    # MySQL configuration
    DATABASE_HOST = os.getenv("DATABASE_HOST", "127.0.0.1")
    DATABASE_PORT = int(os.getenv("DATABASE_PORT", "3306"))
    DATABASE_NAME = os.getenv("DATABASE_NAME", "omniguard_db")
    DATABASE_USER = os.getenv("DATABASE_USER", "root")
    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "")

    # JWT configuration
    JWT_SECRET = os.getenv("JWT_SECRET", "")
    JWT_EXPIRE_MINUTES = int(
        os.getenv("JWT_EXPIRE_MINUTES", "60")
    )

    # React + Vite frontend origins
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ]


settings = Settings()
