"""Admin user model (staff only — no public clients)."""

from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.mixins import TimestampMixin, utcnow


class Admin(UserMixin, db.Model, TimestampMixin):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_login_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False, index=True)

    role = relationship("Role", back_populates="admins", lazy="joined")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def has_permission(self, code: str) -> bool:
        if not self.is_active or not self.role:
            return False
        return self.role.has_permission(code)

    def has_any_permission(self, *codes: str) -> bool:
        return any(self.has_permission(code) for code in codes)

    @property
    def is_super_admin(self) -> bool:
        return bool(self.role and self.role.slug == "super-admin")

    @property
    def is_locked(self) -> bool:
        return bool(self.locked_until and self.locked_until > utcnow())

    def record_login_success(self) -> None:
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login_at = utcnow()

    def record_login_failure(self, max_attempts: int = 5, lock_minutes: int = 15) -> None:
        from datetime import timedelta

        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.locked_until = utcnow() + timedelta(minutes=lock_minutes)

    def get_id(self) -> str:
        return str(self.id)

    def __repr__(self) -> str:
        return f"<Admin {self.email}>"
