"""Destination model."""

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class Destination(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "destinations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), unique=True, nullable=False, index=True)
    short_description: Mapped[str | None] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    attractions: Mapped[str | None] = mapped_column(Text)
    travel_info: Mapped[str | None] = mapped_column(Text)
    hero_image: Mapped[str | None] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(String(120))
    region: Mapped[str | None] = mapped_column(String(120))
    map_embed_url: Mapped[str | None] = mapped_column(String(500))
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    seo_title: Mapped[str | None] = mapped_column(String(180))
    seo_description: Mapped[str | None] = mapped_column(String(320))
    og_image: Mapped[str | None] = mapped_column(String(255))

    tours = relationship("Tour", back_populates="destination", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Destination {self.slug}>"
