"""Testimonials / reviews managed by admin (genuine entries only)."""

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import TimestampMixin


class Review(db.Model, TimestampMixin):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(160), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    tour_id: Mapped[int | None] = mapped_column(ForeignKey("tours.id"), index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    tour = relationship("Tour", back_populates="reviews", lazy="joined")
