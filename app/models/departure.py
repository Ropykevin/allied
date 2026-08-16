"""Tour departure / schedule model with capacity tracking."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import TimestampMixin


class Departure(db.Model, TimestampMixin):
    __tablename__ = "departures"
    __table_args__ = (
        UniqueConstraint("tour_id", "departure_date", name="uq_tour_departure_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tour_id: Mapped[int] = mapped_column(ForeignKey("tours.id"), nullable=False, index=True)
    departure_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    return_date: Mapped[date | None] = mapped_column(Date)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    price_adult: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    price_child: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="OPEN", index=True
    )  # OPEN, CLOSED, CANCELLED, COMPLETED
    notes: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    tour = relationship("Tour", back_populates="departures", lazy="joined")
    bookings = relationship("Booking", back_populates="departure", lazy="dynamic")

    @property
    def booked_seats(self) -> int:
        """Seats held by non-cancelled bookings."""
        from app.models.booking import Booking

        active = (
            Booking.query.filter(
                Booking.departure_id == self.id,
                Booking.booking_status != "CANCELLED",
            ).all()
        )
        return sum(b.total_travelers for b in active)

    @property
    def available_seats(self) -> int:
        return max(self.capacity - self.booked_seats, 0)

    @property
    def is_bookable(self) -> bool:
        today = date.today()
        return (
            self.is_active
            and self.status == "OPEN"
            and self.departure_date >= today
            and self.available_seats > 0
        )

    def __repr__(self) -> str:
        return f"<Departure tour={self.tour_id} date={self.departure_date}>"
