"""Testing configuration."""

from datetime import timedelta


class TestingConfig:
    DEBUG = False
    TESTING = True
    SECRET_KEY = "testing-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    LOGIN_DISABLED = False
    SERVER_NAME = "localhost.localdomain"
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    REMEMBER_COOKIE_DURATION = timedelta(days=1)
    MAIL_SUPPRESS_SEND = True
    MAIL_DEFAULT_SENDER = "test@alliedtours.example"
    COMPANY_NAME = "Allied Tours & Travel"
    COMPANY_TAGLINE = "Your one-stop travel shop."
    COMPANY_EMAIL = "info@alliedtravelke.com"
    COMPANY_PHONE = "+254 724 506 787"
    COMPANY_PHONE_SECONDARY = "+254 720 688 665"
    COMPANY_WHATSAPP = "+254724506787"
    COMPANY_ADDRESS = "P.O. Box 102163-002100, Nairobi"
    COMPANY_OFFICE = "Uniafric House, 1st Floor, 141 Koinange Street, Nairobi"
    COMPANY_CURRENCY = "KES"
    SOCIAL_FACEBOOK = ""
    SOCIAL_INSTAGRAM = ""
    SOCIAL_TWITTER = ""
    SOCIAL_YOUTUBE = ""
    UPLOAD_FOLDER = "instance/test_uploads"
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    RATELIMIT_ENABLED = False
    RATELIMIT_STORAGE_URI = "memory://"
