"""Loads settings from the .env file so secrets never live in the code."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"
load_dotenv(BASE_DIR / ".env")


class Settings:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "120"))
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "pocketsmart.db"))
    ALLOWED_ORIGINS = [
        o.strip()
        for o in os.getenv(
            "ALLOWED_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000"
        ).split(",")
    ]


settings = Settings()
