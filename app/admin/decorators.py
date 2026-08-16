"""Admin authorization decorators."""

from functools import wraps

from flask import abort, redirect, request, url_for
from flask_login import current_user


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login", next=request.path))
        if not getattr(current_user, "is_active", False):
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def permission_required(*codes: str):
    """Require one or more permission codes (OR logic)."""

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login", next=request.path))
            if not any(current_user.has_permission(code) for code in codes):
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator
