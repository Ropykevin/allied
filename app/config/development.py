"""Development configuration."""

import os
from datetime import timedelta


class DevelopmentConfig:
    DEBUG = True
    TESTING = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://allied:allied_secret@localhost:5432/allied_tours",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = False
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    MAIL_SERVER = os.getenv("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "1025"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "False").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv(
        "MAIL_DEFAULT_SENDER", "Allied Tours & Travel <noreply@localhost>"
    )

    COMPANY_NAME = os.getenv("COMPANY_NAME", "Allied Tours & Travel")
    COMPANY_TAGLINE = os.getenv("COMPANY_TAGLINE", "Your one-stop travel shop.")
    COMPANY_EMAIL = os.getenv("COMPANY_EMAIL", "info@alliedtravelke.com")
    COMPANY_PHONE = os.getenv("COMPANY_PHONE", "+254 724 506 787")
    COMPANY_PHONE_SECONDARY = os.getenv("COMPANY_PHONE_SECONDARY", "+254 720 688 665")
    COMPANY_WHATSAPP = os.getenv("COMPANY_WHATSAPP", "+254724506787")
    COMPANY_ADDRESS = os.getenv(
        "COMPANY_ADDRESS", "P.O. Box 102163-002100, Nairobi"
    )
    COMPANY_OFFICE = os.getenv(
        "COMPANY_OFFICE",
        "Uniafric House, 1st Floor, 141 Koinange Street, Nairobi",
    )
    COMPANY_CURRENCY = os.getenv("COMPANY_CURRENCY", "KES")
    SOCIAL_FACEBOOK = os.getenv("SOCIAL_FACEBOOK", "")
    SOCIAL_INSTAGRAM = os.getenv("SOCIAL_INSTAGRAM", "")
    SOCIAL_TWITTER = os.getenv("SOCIAL_TWITTER", "")
    SOCIAL_YOUTUBE = os.getenv("SOCIAL_YOUTUBE", "")
    SOCIAL_TRIPADVISOR = os.getenv("SOCIAL_TRIPADVISOR", "")
    GOOGLE_SITE_VERIFICATION = os.getenv(
        "GOOGLE_SITE_VERIFICATION",
        "ajC1R_45-SLiI2qSeOy-V5c2lJurjySBl6LQNI2vbeo",
    )

    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "app/static/uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(100 * 1024 * 1024)))
    MAX_VIDEO_BYTES = int(os.getenv("MAX_VIDEO_BYTES", str(100 * 1024 * 1024)))
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    ALLOWED_VIDEO_EXTENSIONS = {"mp4", "webm", "mov"}

    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_DEFAULT = "200 per hour"
