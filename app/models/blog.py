"""Blog models."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import TimestampMixin

blog_post_tags = Table(
    "blog_post_tags",
    db.Model.metadata,
    Column("post_id", Integer, ForeignKey("blog_posts.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("blog_tags.id", ondelete="CASCADE"), primary_key=True),
)


class BlogCategory(db.Model, TimestampMixin):
    __tablename__ = "blog_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(140), unique=True, nullable=False, index=True)

    posts = relationship("BlogPost", back_populates="category", lazy="dynamic")


class BlogTag(db.Model, TimestampMixin):
    __tablename__ = "blog_tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    posts = relationship("BlogPost", secondary=blog_post_tags, back_populates="tags")


class BlogPost(db.Model, TimestampMixin):
    __tablename__ = "blog_posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    slug: Mapped[str] = mapped_column(String(240), unique=True, nullable=False, index=True)
    excerpt: Mapped[str | None] = mapped_column(String(400))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    featured_image: Mapped[str | None] = mapped_column(String(255))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("blog_categories.id"))
    author_id: Mapped[int | None] = mapped_column(ForeignKey("admins.id"))
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    seo_title: Mapped[str | None] = mapped_column(String(180))
    seo_description: Mapped[str | None] = mapped_column(String(320))
    og_image: Mapped[str | None] = mapped_column(String(255))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    category = relationship("BlogCategory", back_populates="posts", lazy="joined")
    author = relationship("Admin", lazy="joined")
    tags = relationship("BlogTag", secondary=blog_post_tags, back_populates="posts", lazy="selectin")
