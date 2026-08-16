"""Site settings management."""

from flask import flash, redirect, render_template, url_for
from flask_login import login_required

from app.admin import bp
from app.admin.decorators import permission_required
from app.admin.forms import SettingsForm
from app.extensions import db
from app.models import Setting
from app.utils.audit import log_action


def _get_setting(key: str, default: str = "") -> str:
    row = Setting.query.filter_by(key=key).first()
    return row.value if row and row.value is not None else default


def _set_setting(key: str, value: str, description: str = "") -> None:
    row = Setting.query.filter_by(key=key).first()
    if not row:
        row = Setting(key=key, description=description)
        db.session.add(row)
    row.value = value


@bp.route("/settings", methods=["GET", "POST"])
@login_required
@permission_required("settings.view")
def settings_page():
    form = SettingsForm()
    if form.validate_on_submit():
        if not form and False:
            pass
    if form.validate_on_submit():
        from flask_login import current_user

        if not current_user.has_permission("settings.update"):
            flash("You cannot update settings.", "danger")
            return redirect(url_for("admin.settings_page"))
        _set_setting("company_email", form.company_email.data or "", "Public company email")
        _set_setting("company_phone", form.company_phone.data or "", "Public company phone")
        _set_setting("company_address", form.company_address.data or "", "Company address")
        _set_setting(
            "payment_instructions",
            form.payment_instructions.data or "",
            "Default invoice payment instructions",
        )
        db.session.commit()
        log_action("settings.updated", "settings", None)
        flash("Settings saved.", "success")
        return redirect(url_for("admin.settings_page"))

    if not form.is_submitted():
        form.company_email.data = _get_setting("company_email")
        form.company_phone.data = _get_setting("company_phone")
        form.company_address.data = _get_setting("company_address")
        form.payment_instructions.data = _get_setting("payment_instructions")

    return render_template("admin/settings.html", form=form)
