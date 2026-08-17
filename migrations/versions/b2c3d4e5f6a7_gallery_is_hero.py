"""gallery is_hero for homepage hero slideshow

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-17 18:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("gallery", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("is_hero", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch_op.create_index(batch_op.f("ix_gallery_is_hero"), ["is_hero"], unique=False)


def downgrade():
    with op.batch_alter_table("gallery", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_gallery_is_hero"))
        batch_op.drop_column("is_hero")
