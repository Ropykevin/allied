"""Tour and related content models."""

from decimal import Decimal

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class Tour(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "tours"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False, index=True)
    short_description: Mapped[str | None] = mapped_column(String(400))
    overview: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(80), index=True)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    duration_nights: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    starting_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="KES")
    default_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    pickup_info: Mapped[str | None] = mapped_column(Text)
    hero_image: Mapped[str | None] = mapped_column(String(255))
    map_embed_url: Mapped[str | None] = mapped_column(String(500))
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    destination_id: Mapped[int] = mapped_column(
        ForeignKey("destinations.id"), nullable=False, index=True
    )
    seo_title: Mapped[str | None] = mapped_column(String(180))
    seo_description: Mapped[str | None] = mapped_column(String(320))
    og_image: Mapped[str | None] = mapped_column(String(255))

    destination = relationship("Destination", back_populates="tours", lazy="joined")
    images = relationship(
        "TourImage",
        back_populates="tour",
        cascade="all, delete-orphan",
        order_by="TourImage.sort_order",
        lazy="selectin",
    )
    itineraries = relationship(
        "TourItinerary",
        back_populates="tour",
        cascade="all, delete-orphan",
        order_by="TourItinerary.day_number",
        lazy="selectin",
    )
    inclusions = relationship(
        "TourInclusion",
        back_populates="tour",
        cascade="all, delete-orphan",
        order_by="TourInclusion.sort_order",
        lazy="selectin",
    )
    exclusions = relationship(
        "TourExclusion",
        back_populates="tour",
        cascade="all, delete-orphan",
        order_by="TourExclusion.sort_order",
        lazy="selectin",
    )
    faqs = relationship(
        "TourFAQ",
        back_populates="tour",
        cascade="all, delete-orphan",
        order_by="TourFAQ.sort_order",
        lazy="selectin",
    )
    departures = relationship("Departure", back_populates="tour", lazy="dynamic")
    reviews = relationship("Review", back_populates="tour", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Tour {self.slug}>"


class TourImage(db.Model, TimestampMixin):
    __tablename__ = "tour_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    tour_id: Mapped[int] = mapped_column(ForeignKey("tours.id", ondelete="CASCADE"), index=True)
    image_path: Mapped[str] = mapped_column(String(255), nullable=False)
    alt_text: Mapped[str | None] = mapped_column(String(200))
    caption: Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    tour = relationship("Tour", back_populates="images")


class TourItinerary(db.Model, TimestampMixin):
    __tablename__ = "tour_itineraries"
    __table_args__ = (UniqueConstraint("tour_id", "day_number", name="uq_tour_day"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tour_id: Mapped[int] = mapped_column(ForeignKey("tours.id", ondelete="CASCADE"), index=True)
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    tour = relationship("Tour", back_populates="itineraries")


class TourInclusion(db.Model, TimestampMixin):
    __tablename__ = "tour_inclusions"

    id: Mapped[int] = mapped_column(primary_key=True)
    tour_id: Mapped[int] = mapped_column(ForeignKey("tours.id", ondelete="CASCADE"), index=True)
    item: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    tour = relationship("Tour", back_populates="inclusions")


class TourExclusion(db.Model, TimestampMixin):
    __tablename__ = "tour_exclusions"

    id: Mapped[int] = mapped_column(primary_key=True)
    tour_id: Mapped[int] = mapped_column(ForeignKey("tours.id", ondelete="CASCADE"), index=True)
    item: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    tour = relationship("Tour", back_populates="exclusions")


class TourFAQ(db.Model, TimestampMixin):
    __tablename__ = "tour_faqs"

    id: Mapped[int] = mapped_column(primary_key=True)
    tour_id: Mapped[int] = mapped_column(ForeignKey("tours.id", ondelete="CASCADE"), index=True)
    question: Mapped[str] = mapped_column(String(300), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    tour = relationship("Tour", back_populates="faqs")


class FAQ(db.Model, TimestampMixin):
    """Global FAQs for the public FAQ page."""

    __tablename__ = "faqs"

    id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[str] = mapped_column(String(300), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(80))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
