"""Travel services offered by Allied Tours & Travel."""

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import TimestampMixin


class Service(db.Model, TimestampMixin):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), unique=True, nullable=False, index=True)
    short_description: Mapped[str | None] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    overview: Mapped[str | None] = mapped_column(Text)
    highlights: Mapped[str | None] = mapped_column(Text)  # one item per line
    what_is_included: Mapped[str | None] = mapped_column(Text)
    how_it_works: Mapped[str | None] = mapped_column(Text)
    who_its_for: Mapped[str | None] = mapped_column(Text)
    important_notes: Mapped[str | None] = mapped_column(Text)
    icon_image: Mapped[str | None] = mapped_column(String(255))
    hero_image: Mapped[str | None] = mapped_column(String(255))
    seo_title: Mapped[str | None] = mapped_column(String(200))
    seo_description: Mapped[str | None] = mapped_column(String(320))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_bookable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    bookings = relationship("Booking", back_populates="service", lazy="dynamic")

    def lines(self, field: str) -> list[str]:
        raw = getattr(self, field, None) or ""
        return [line.strip() for line in raw.splitlines() if line.strip()]

    def __repr__(self) -> str:
        return f"<Service {self.slug}>"
