"""Admin authentication blueprint."""

from flask import Blueprint

bp = Blueprint("auth", __name__, url_prefix="/admin")

from app.auth import routes  # noqa: E402, F401
