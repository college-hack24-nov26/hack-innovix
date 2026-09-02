import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-medikiosk-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'medikiosk.db'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))
    UPLOAD_FOLDER = BASE_DIR / os.getenv("UPLOAD_FOLDER", "uploads")
    AI_PROVIDER = os.getenv("AI_PROVIDER", "mock")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OCR_PROVIDER = os.getenv("OCR_PROVIDER", "mock")
    DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
    SESSION_TIMEOUT_SECONDS = int(os.getenv("SESSION_TIMEOUT_SECONDS", "300"))
    CONSENT_VERSION = os.getenv("CONSENT_VERSION", "1.0")
    ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}
    ALLOWED_MIME = {"application/pdf", "image/jpeg", "image/png"}
    SUPPORTED_LANGUAGES = ("en", "hi", "mr")
    DEFAULT_LANGUAGE = "en"


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    DEMO_MODE = True
