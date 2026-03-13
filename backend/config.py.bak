import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""
    JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "1"))
    PORT = int(os.getenv("PORT", "5000"))
    DATABASE_URL = os.getenv("DATABASE_URL", os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "notes.db"
    ))
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5000").split(",")
    TITLE_MAX_LENGTH = 200
    CONTENT_MAX_LENGTH = 50000
