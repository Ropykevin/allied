"""Booking and passenger models."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import TimestampMixin


class Booking(db.Model, TimestampMixin):
    __tablename__ = "bookings"
    __table_args__ = (UniqueConstraint("reference", name="uq_booking_reference"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    booking_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="TOUR", index=True
    )
    # TOUR | SERVICE
    tour_id: Mapped[int | None] = mapped_column(ForeignKey("tours.id"), nullable=True, index=True)
    departure_id: Mapped[int | None] = mapped_column(
        ForeignKey("departures.id"), nullable=True, index=True
    )
    service_id: Mapped[int | None] = mapped_column(
        ForeignKey("services.id"), nullable=True, index=True
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"), nullable=False, index=True
    )
    adults: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    children: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    preferred_travel_date: Mapped[date | None] = mapped_column(Date)
    destination_country: Mapped[str | None] = mapped_column(String(120))
    pickup_location: Mapped[str | None] = mapped_column(String(255))
    special_requests: Mapped[str | None] = mapped_column(Text)
    booking_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="NEW", index=True
    )
    # NEW, UNDER_REVIEW, INVOICED, CONFIRMED, CANCELLED, COMPLETED
    payment_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="UNPAID", index=True
    )
    # UNPAID, PARTIALLY_PAID, PAID, REFUNDED
    estimated_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="KES")
    admin_notes: Mapped[str | None] = mapped_column(Text)
    submission_token: Mapped[str | None] = mapped_column(String(64), index=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    tour = relationship("Tour", lazy="joined")
    departure = relationship("Departure", back_populates="bookings", lazy="joined")
    service = relationship("Service", back_populates="bookings", lazy="joined")
    customer = relationship("Customer", back_populates="bookings", lazy="joined")
    passengers = relationship(
        "BookingPassenger",
        back_populates="booking",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    invoices = relationship("Invoice", back_populates="booking", lazy="selectin")

    @property
    def is_service_booking(self) -> bool:
        return (self.booking_type or "TOUR").upper() == "SERVICE"

    @property
    def display_title(self) -> str:
        if self.is_service_booking and self.service:
            return self.service.name
        if self.tour:
            return self.tour.name
        return "Booking"

    @property
    def total_travelers(self) -> int:
        return int(self.adults or 0) + int(self.children or 0)

    @property
    def latest_invoice(self):
        if not self.invoices:
            return None
        return sorted(self.invoices, key=lambda i: i.created_at, reverse=True)[0]

    def __repr__(self) -> str:
        return f"<Booking {self.reference}>"


class BookingPassenger(db.Model, TimestampMixin):
    __tablename__ = "booking_passengers"

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    passenger_type: Mapped[str] = mapped_column(String(20), nullable=False, default="ADULT")
    # ADULT, CHILD
    age: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(String(255))

    booking = relationship("Booking", back_populates="passengers")
