"""Internal admin notifications."""

from __future__ import annotations

from app.extensions import db
from app.models import Admin, Notification


class NotificationService:
    @staticmethod
    def notify_admins(
        title: str,
        message: str,
        link: str | None = None,
        category: str = "general",
        permission: str | None = None,
    ) -> None:
        query = Admin.query.filter_by(is_active=True)
        admins = query.all()
        for admin in admins:
            if permission and not admin.has_permission(permission):
                continue
            db.session.add(
                Notification(
                    admin_id=admin.id,
                    title=title,
                    message=message,
                    link=link,
                    category=category,
                )
            )
        db.session.commit()
