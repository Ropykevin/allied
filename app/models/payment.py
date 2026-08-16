"""Payment model — manual recording now; gateway-ready fields for future."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import TimestampMixin


class Payment(db.Model, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id"), nullable=False, index=True
    )
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="KES")
    method: Mapped[str] = mapped_column(String(40), nullable=False)
    # M-Pesa, Bank Transfer, Cash, Card, Other
    transaction_reference: Mapped[str | None] = mapped_column(String(120), index=True)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="RECORDED", index=True
    )
    # RECORDED, VERIFIED, REFUNDED, FAILED
    provider: Mapped[str] = mapped_column(String(40), nullable=False, default="manual")
    # manual | mpesa | paystack | stripe (future)
    provider_payment_id: Mapped[str | None] = mapped_column(String(120), index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    recorded_by_id: Mapped[int | None] = mapped_column(ForeignKey("admins.id"))
    verified_by_id: Mapped[int | None] = mapped_column(ForeignKey("admins.id"))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    invoice = relationship("Invoice", back_populates="payments", lazy="joined")
    booking = relationship("Booking", lazy="joined")
    recorded_by = relationship("Admin", foreign_keys=[recorded_by_id], lazy="joined")
    verified_by = relationship("Admin", foreign_keys=[verified_by_id], lazy="joined")

    def __repr__(self) -> str:
        return f"<Payment {self.id} {self.amount} {self.method}>"
