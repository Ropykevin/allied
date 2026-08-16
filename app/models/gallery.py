"""Gallery image model."""

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.models.mixins import TimestampMixin


class GalleryImage(db.Model, TimestampMixin):
    __tablename__ = "gallery"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    image_path: Mapped[str] = mapped_column(String(255), nullable=False)
    alt_text: Mapped[str | None] = mapped_column(String(200))
    category: Mapped[str | None] = mapped_column(String(80), index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
