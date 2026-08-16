"""Audit logging helper."""

from __future__ import annotations

from flask import request
from flask_login import current_user

from app.extensions import db
from app.models import AuditLog


def log_action(
    action: str,
    entity: str | None = None,
    entity_id: int | None = None,
    details: str | None = None,
) -> None:
    admin_id = current_user.id if getattr(current_user, "is_authenticated", False) else None
    entry = AuditLog(
        admin_id=admin_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        details=details,
        ip_address=request.remote_addr if request else None,
        user_agent=(request.headers.get("User-Agent", "")[:300] if request else None),
    )
    db.session.add(entry)
