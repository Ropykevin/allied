"""Invoice and line-item models."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import TimestampMixin


class Invoice(db.Model, TimestampMixin):
    __tablename__ = "invoices"
    __table_args__ = (UniqueConstraint("invoice_number", name="uq_invoice_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_number: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id"), nullable=False, index=True
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"), nullable=False, index=True
    )
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="DRAFT", index=True
    )
    # DRAFT, SENT, PARTIALLY_PAID, PAID, VOID, OVERDUE
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    discount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="KES")
    payment_instructions: Mapped[str | None] = mapped_column(Text)
    terms: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pdf_path: Mapped[str | None] = mapped_column(String(255))
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("admins.id"))

    booking = relationship("Booking", back_populates="invoices", lazy="joined")
    customer = relationship("Customer", lazy="joined")
    items = relationship(
        "InvoiceItem",
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="InvoiceItem.sort_order",
        lazy="selectin",
    )
    payments = relationship(
        "Payment",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    created_by = relationship("Admin", lazy="joined")

    @property
    def balance(self) -> Decimal:
        return (self.total or Decimal("0")) - (self.amount_paid or Decimal("0"))

    def recalculate_totals(self) -> None:
        self.subtotal = sum((item.line_total for item in self.items), Decimal("0"))
        self.total = self.subtotal - (self.discount or Decimal("0")) + (self.tax or Decimal("0"))
        if self.total < 0:
            self.total = Decimal("0")

    def sync_payment_totals(self) -> None:
        # Query fresh rows so newly flushed payments are included
        from app.models.payment import Payment

        payments = Payment.query.filter_by(invoice_id=self.id).all()
        paid = sum(
            (p.amount for p in payments if p.status in ("RECORDED", "VERIFIED")),
            Decimal("0"),
        )
        refunded = sum(
            (p.amount for p in payments if p.status == "REFUNDED"),
            Decimal("0"),
        )
        self.amount_paid = paid - refunded
        if self.amount_paid <= 0:
            self.amount_paid = Decimal("0")
            self.status = "SENT" if self.sent_at else "DRAFT"
        elif self.amount_paid < self.total:
            self.status = "PARTIALLY_PAID"
        else:
            self.status = "PAID"

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number}>"


class InvoiceItem(db.Model, TimestampMixin):
    __tablename__ = "invoice_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    invoice = relationship("Invoice", back_populates="items")

    def compute_line_total(self) -> None:
        self.line_total = Decimal(self.quantity) * (self.unit_price or Decimal("0"))
