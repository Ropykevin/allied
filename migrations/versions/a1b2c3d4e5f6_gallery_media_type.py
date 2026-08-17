"""gallery media_type for video uploads

Revision ID: a1b2c3d4e5f6
Revises: 5d75a19aa41d
Create Date: 2026-08-17 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "5d75a19aa41d"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("gallery", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("media_type", sa.String(length=20), nullable=False, server_default="image")
        )
        batch_op.create_index(batch_op.f("ix_gallery_media_type"), ["media_type"], unique=False)


def downgrade():
    with op.batch_alter_table("gallery", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_gallery_media_type"))
        batch_op.drop_column("media_type")
