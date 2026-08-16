"""Customer records (no authentication — booking contacts only)."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import TimestampMixin


class Customer(db.Model, TimestampMixin):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    country: Mapped[str | None] = mapped_column(String(120))

    bookings = relationship("Booking", back_populates="customer", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Customer {self.email}>"
