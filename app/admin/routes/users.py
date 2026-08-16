"""Admin user and audit log management."""

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.admin import bp
from app.admin.decorators import permission_required
from app.admin.forms import AdminUserForm, RolePermissionsForm
from app.extensions import db
from app.models import Admin, AuditLog, Permission, Role
from app.utils.audit import log_action
from app.utils.permissions import PERMISSIONS


def _role_choices_for(actor: Admin) -> list[tuple[int, str]]:
    roles = Role.query.order_by(Role.name).all()
    if actor.is_super_admin:
        return [(r.id, r.name) for r in roles]
    # Non–super-admins cannot assign Super Admin.
    return [(r.id, r.name) for r in roles if r.slug != "super-admin"]


def _count_active_super_admins() -> int:
    return (
        Admin.query.join(Role)
        .filter(Role.slug == "super-admin", Admin.is_active.is_(True))
        .count()
    )


def _super_admin_role() -> Role | None:
    return Role.query.filter_by(slug="super-admin").first()


@bp.route("/users")
@login_required
@permission_required("admins.view")
def users_list():
    admins = Admin.query.order_by(Admin.full_name).all()
    return render_template("admin/users/list.html", admins=admins)


@bp.route("/users/new", methods=["GET", "POST"])
@login_required
@permission_required("admins.create")
def users_create():
    form = AdminUserForm()
    form.role_id.choices = _role_choices_for(current_user)
    if form.validate_on_submit():
        if not form.password.data:
            flash("Password is required for new admins.", "danger")
        elif Admin.query.filter_by(email=form.email.data.lower().strip()).first():
            flash("Email already in use.", "danger")
        else:
            role = db.session.get(Role, form.role_id.data)
            if role and role.slug == "super-admin" and not current_user.is_super_admin:
                flash("Only a Super Admin can assign the Super Admin role.", "danger")
            else:
                admin = Admin(
                    full_name=form.full_name.data,
                    email=form.email.data.lower().strip(),
                    role_id=form.role_id.data,
                    is_active=form.is_active.data,
                )
                admin.set_password(form.password.data)
                db.session.add(admin)
                db.session.commit()
                log_action("admin.created", "admin", admin.id, admin.email)
                flash("Admin user created.", "success")
                return redirect(url_for("admin.users_list"))
    return render_template("admin/users/form.html", form=form, admin=None)


@bp.route("/users/<int:admin_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("admins.update")
def users_edit(admin_id: int):
    admin = Admin.query.get_or_404(admin_id)
    form = AdminUserForm(obj=admin)
    form.role_id.choices = _role_choices_for(current_user)
    if form.validate_on_submit():
        new_role = db.session.get(Role, form.role_id.data)
        if new_role and new_role.slug == "super-admin" and not current_user.is_super_admin:
            flash("Only a Super Admin can assign the Super Admin role.", "danger")
            return render_template("admin/users/form.html", form=form, admin=admin)

        was_super = admin.is_super_admin
        will_be_super = bool(new_role and new_role.slug == "super-admin")
        will_be_active = bool(form.is_active.data)

        # Prevent removing the last active Super Admin.
        if was_super and admin.is_active and (not will_be_super or not will_be_active):
            if _count_active_super_admins() <= 1:
                flash("Cannot remove or deactivate the last active Super Admin.", "danger")
                return render_template("admin/users/form.html", form=form, admin=admin)

        # Avoid locking yourself out of admin management.
        if admin.id == current_user.id and not will_be_active:
            flash("You cannot deactivate your own account.", "danger")
            return render_template("admin/users/form.html", form=form, admin=admin)

        if admin.id == current_user.id and new_role and not new_role.has_permission("admins.update"):
            flash("You cannot remove your own ability to manage admin users.", "danger")
            return render_template("admin/users/form.html", form=form, admin=admin)

        admin.full_name = form.full_name.data
        admin.email = form.email.data.lower().strip()
        admin.role_id = form.role_id.data
        admin.is_active = form.is_active.data
        if form.password.data:
            admin.set_password(form.password.data)
        db.session.commit()
        log_action("admin.updated", "admin", admin.id, admin.email)
        flash("Admin updated.", "success")
        return redirect(url_for("admin.users_list"))
    return render_template("admin/users/form.html", form=form, admin=admin)


@bp.route("/users/<int:admin_id>/deactivate", methods=["POST"])
@login_required
@permission_required("admins.delete")
def users_deactivate(admin_id: int):
    admin = Admin.query.get_or_404(admin_id)
    if admin.id == current_user.id:
        flash("You cannot deactivate your own account.", "danger")
        return redirect(url_for("admin.users_list"))
    if admin.is_super_admin and admin.is_active and _count_active_super_admins() <= 1:
        flash("Cannot deactivate the last active Super Admin.", "danger")
        return redirect(url_for("admin.users_list"))
    admin.is_active = False
    db.session.commit()
    log_action("admin.deactivated", "admin", admin.id, admin.email)
    flash(f"{admin.full_name} has been deactivated.", "success")
    return redirect(url_for("admin.users_list"))


@bp.route("/roles")
@login_required
@permission_required("admins.view")
def roles_list():
    roles = Role.query.order_by(Role.name).all()
    return render_template(
        "admin/users/roles.html",
        roles=roles,
        can_edit_roles=current_user.has_permission("admins.update"),
    )


@bp.route("/roles/<int:role_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("admins.update")
def roles_edit(role_id: int):
    if not current_user.is_super_admin:
        abort(403)
    role = Role.query.get_or_404(role_id)
    form = RolePermissionsForm()
    all_permissions = Permission.query.order_by(Permission.category, Permission.code).all()
    grouped: dict[str, list[Permission]] = {}
    for perm in all_permissions:
        grouped.setdefault(perm.category, []).append(perm)

    if form.validate_on_submit():
        selected_codes = set(request.form.getlist("permission_codes"))
        # Super Admin must keep core admin management permissions.
        if role.slug == "super-admin":
            required = {"admins.view", "admins.create", "admins.update", "admins.delete"}
            selected_codes |= required

        selected = Permission.query.filter(Permission.code.in_(selected_codes)).all() if selected_codes else []
        role.permissions = selected
        db.session.commit()
        log_action("role.permissions_updated", "role", role.id, role.slug)
        flash(f"Permissions updated for {role.name}.", "success")
        return redirect(url_for("admin.roles_list"))

    selected_codes = {p.code for p in role.permissions}
    return render_template(
        "admin/users/role_edit.html",
        form=form,
        role=role,
        grouped_permissions=grouped,
        selected_codes=selected_codes,
        catalog=PERMISSIONS,
    )


@bp.route("/audit-logs")
@login_required
@permission_required("audit_logs.view")
def audit_logs():
    page = request.args.get("page", 1, type=int)
    pagination = AuditLog.query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    return render_template(
        "admin/users/audit_logs.html", pagination=pagination, logs=pagination.items
    )
