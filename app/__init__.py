"""Allied Tours & Travel application factory."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_login import current_user

from app.config import get_config
from app.extensions import csrf, db, limiter, login_manager, mail, migrate


def create_app(config_name: str | None = None) -> Flask:
    load_dotenv(override=True)
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder="static",
        template_folder="templates",
    )
    config_obj = get_config(config_name or os.getenv("FLASK_ENV", "development"))
    app.config.from_object(config_obj)

    env_name = (config_name or os.getenv("FLASK_ENV", "development")).lower()
    if env_name == "production":
        secret = app.config.get("SECRET_KEY") or ""
        if len(secret) < 32:
            raise RuntimeError("SECRET_KEY must be at least 32 characters in production.")
        if not app.config.get("SQLALCHEMY_DATABASE_URI"):
            raise RuntimeError("DATABASE_URL is required in production.")

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    upload_folder = Path(app.config["UPLOAD_FOLDER"])
    if not upload_folder.is_absolute():
        upload_folder = Path(app.root_path).parent / upload_folder
        # Prefer app/static/uploads when relative path points there
        if str(app.config["UPLOAD_FOLDER"]).startswith("app/"):
            upload_folder = Path(app.root_path).parent / app.config["UPLOAD_FOLDER"]
    upload_folder.mkdir(parents=True, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = str(upload_folder)

    _configure_logging(app)
    _init_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_context_processors(app)
    _register_cli(app)

    return app


def _configure_logging(app: Flask) -> None:
    if not app.debug and not app.testing:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)


def _init_extensions(app: Flask) -> None:
    # Trust X-Forwarded-* when behind a reverse proxy (set TRUST_PROXY_HOPS>=1).
    hops = int(os.getenv("TRUST_PROXY_HOPS", "0") or "0")
    if hops > 0:
        from werkzeug.middleware.proxy_fix import ProxyFix

        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=hops, x_proto=hops, x_host=hops, x_prefix=hops)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    @app.after_request
    def set_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=()",
        )
        csp = (
            "default-src 'self'; "
            "img-src 'self' data: https://images.unsplash.com https://*.google.com https://*.gstatic.com; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; "
            "font-src 'self' data:; "
            "frame-src 'self' https://www.google.com https://maps.google.com; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'self'"
        )
        response.headers.setdefault("Content-Security-Policy", csp)
        if not app.debug and app.config.get("PREFERRED_URL_SCHEME") == "https":
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        return response

    from app.utils.sanitize import (
        plain_text_to_html,
        safe_external_url,
        safe_map_embed_url,
        sanitize_html,
    )

    app.jinja_env.filters["sanitize_html"] = sanitize_html
    app.jinja_env.filters["plain_text_html"] = plain_text_to_html
    app.jinja_env.filters["safe_url"] = safe_external_url
    app.jinja_env.filters["safe_map_url"] = safe_map_embed_url

    # Import models after Flask app bindings — avoid shadowing local `app` name.
    import importlib

    importlib.import_module("app.models")
    from app.models import Admin  # noqa: WPS433

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(Admin, int(user_id))

def _register_blueprints(app: Flask) -> None:
    from app.admin import bp as admin_bp
    from app.auth import bp as auth_bp
    from app.public import bp as public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")


def _register_error_handlers(app: Flask) -> None:
    def _error_page(error, code: int):
        template = f"errors/{code}.html"
        return render_template(template), code

    @app.errorhandler(400)
    def bad_request(error):
        return _error_page(error, 400)

    @app.errorhandler(401)
    def unauthorized(error):
        return _error_page(error, 401)

    @app.errorhandler(403)
    def forbidden(error):
        return _error_page(error, 403)

    @app.errorhandler(404)
    def not_found(error):
        return _error_page(error, 404)

    @app.errorhandler(429)
    def too_many(error):
        return _error_page(error, 429)

    @app.errorhandler(500)
    def server_error(error):
        app.logger.exception("Server error: %s", error)
        return _error_page(error, 500)


def _register_context_processors(app: Flask) -> None:
    DEFAULT_HERO = (
        "https://images.unsplash.com/photo-1516426122078-c23e76319801"
        "?auto=format&fit=crop&w=1920&q=80"
    )

    @app.context_processor
    def inject_globals():
        from flask import request, url_for

        from app.models import GalleryImage

        def _gallery_paths() -> list[str]:
            try:
                rows = (
                    GalleryImage.query.filter(GalleryImage.is_published.is_(True))
                    .order_by(
                        GalleryImage.is_featured.desc(),
                        GalleryImage.sort_order,
                        GalleryImage.id.desc(),
                    )
                    .limit(24)
                    .all()
                )
                return [r.image_path for r in rows if r.image_path]
            except Exception:  # noqa: BLE001 — DB may not be ready during some CLI tasks
                return []

        def page_hero_image(prefer: str | None = None) -> str | None:
            """Prefer an explicit image, else a stable gallery photo for this path."""
            if prefer:
                return prefer
            paths = _gallery_paths()
            if not paths:
                return None
            key = (request.path if request else "/") or "/"
            idx = sum(ord(c) for c in key) % len(paths)
            return paths[idx]

        def hero_image_url(prefer: str | None = None) -> str:
            """Absolute URL or static URL suitable for <img src>."""
            path = page_hero_image(prefer)
            if not path:
                return DEFAULT_HERO
            if path.startswith("http://") or path.startswith("https://"):
                return path
            return url_for("static", filename=path)

        def whatsapp_url() -> str | None:
            raw = (
                app.config.get("COMPANY_WHATSAPP")
                or app.config.get("COMPANY_PHONE")
                or ""
            )
            digits = "".join(ch for ch in str(raw) if ch.isdigit())
            if not digits:
                return None
            # Kenya local 07xxxxxxxx -> 2547xxxxxxxx
            if digits.startswith("0") and len(digits) == 10:
                digits = "254" + digits[1:]
            message = (
                "Hello Allied Tours & Travel, I would like to enquire about a tour."
            )
            from urllib.parse import quote

            return f"https://wa.me/{digits}?text={quote(message)}"

        return {
            "company_name": app.config.get("COMPANY_NAME"),
            "company_tagline": app.config.get("COMPANY_TAGLINE"),
            "company_email": app.config.get("COMPANY_EMAIL"),
            "company_phone": app.config.get("COMPANY_PHONE"),
            "company_phone_secondary": app.config.get("COMPANY_PHONE_SECONDARY"),
            "company_address": app.config.get("COMPANY_ADDRESS"),
            "company_office": app.config.get("COMPANY_OFFICE"),
            "company_currency": app.config.get("COMPANY_CURRENCY", "KES"),
            "social_facebook": app.config.get("SOCIAL_FACEBOOK") or None,
            "social_instagram": app.config.get("SOCIAL_INSTAGRAM") or None,
            "social_twitter": app.config.get("SOCIAL_TWITTER") or None,
            "social_youtube": app.config.get("SOCIAL_YOUTUBE") or None,
            "current_user": current_user,
            "page_hero_image": page_hero_image,
            "hero_image_url": hero_image_url,
            "default_hero_image": DEFAULT_HERO,
            "whatsapp_url": whatsapp_url(),
        }


def _register_cli(app: Flask) -> None:
    @app.cli.command("seed")
    def seed_command():
        """Seed roles, permissions, demo content."""
        from scripts.seed import run_seed

        run_seed()
        print("Seed complete.")
