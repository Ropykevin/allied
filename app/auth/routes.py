"""Admin login / logout routes."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from urllib.parse import urlparse

from app.auth import bp
from app.auth.forms import LoginForm
from app.extensions import db, limiter
from app.models import Admin
from app.utils.audit import log_action


def _safe_admin_next(next_url: str | None) -> str | None:
    if not next_url:
        return None
    parsed = urlparse(next_url)
    if parsed.scheme or parsed.netloc:
        return None
    path = parsed.path or ""
    if path == "/admin" or path.startswith("/admin/"):
        return next_url
    return None


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(email=form.email.data.lower().strip()).first()
        # Generic messages — avoid account enumeration / lockout disclosure.
        invalid_msg = "Invalid email or password."
        if not admin or not admin.is_active:
            flash(invalid_msg, "danger")
            return render_template("auth/login.html", form=form), 401

        if admin.is_locked:
            flash(invalid_msg, "danger")
            return render_template("auth/login.html", form=form), 429

        if not admin.check_password(form.password.data):
            admin.record_login_failure()
            db.session.commit()
            flash(invalid_msg, "danger")
            return render_template("auth/login.html", form=form), 401

        admin.record_login_success()
        db.session.commit()
        login_user(admin, remember=form.remember_me.data)
        log_action("admin.login", "admin", admin.id)
        next_url = _safe_admin_next(request.args.get("next"))
        if next_url:
            return redirect(next_url)
        return redirect(url_for("admin.dashboard"))

    return render_template("auth/login.html", form=form)


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    log_action("admin.logout", "admin", current_user.id)
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))
