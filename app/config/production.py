"""Production configuration."""

import os
from datetime import timedelta


class ProductionConfig:
    DEBUG = False
    TESTING = False
    # Validated in create_app when this config is active (avoid import-time KeyError
    # when development/testing simply import this module).
    SECRET_KEY = os.environ.get("SECRET_KEY", "")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
    }

    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=4)
    PREFERRED_URL_SCHEME = "https"

    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")

    COMPANY_NAME = os.getenv("COMPANY_NAME", "Allied Tours & Travel")
    COMPANY_TAGLINE = os.getenv("COMPANY_TAGLINE", "Your one-stop travel shop.")
    COMPANY_EMAIL = os.getenv("COMPANY_EMAIL", "")
    COMPANY_PHONE = os.getenv("COMPANY_PHONE", "")
    COMPANY_PHONE_SECONDARY = os.getenv("COMPANY_PHONE_SECONDARY", "")
    COMPANY_WHATSAPP = os.getenv("COMPANY_WHATSAPP", "")
    COMPANY_ADDRESS = os.getenv("COMPANY_ADDRESS", "")
    COMPANY_OFFICE = os.getenv("COMPANY_OFFICE", "")
    COMPANY_CURRENCY = os.getenv("COMPANY_CURRENCY", "KES")
    SOCIAL_FACEBOOK = os.getenv("SOCIAL_FACEBOOK", "")
    SOCIAL_INSTAGRAM = os.getenv("SOCIAL_INSTAGRAM", "")
    SOCIAL_TWITTER = os.getenv("SOCIAL_TWITTER", "")
    SOCIAL_YOUTUBE = os.getenv("SOCIAL_YOUTUBE", "")
    GOOGLE_SITE_VERIFICATION = os.getenv("GOOGLE_SITE_VERIFICATION", "")

    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "app/static/uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(16 * 1024 * 1024)))
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_DEFAULT = "120 per hour"
