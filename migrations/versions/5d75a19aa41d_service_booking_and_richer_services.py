"""service booking and richer services

Revision ID: 5d75a19aa41d
Revises: 2b2b356ec280
Create Date: 2026-08-11 21:54:47.301820

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5d75a19aa41d'
down_revision = '2b2b356ec280'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('bookings', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('booking_type', sa.String(length=20), nullable=False, server_default='TOUR')
        )
        batch_op.add_column(sa.Column('service_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('preferred_travel_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('destination_country', sa.String(length=120), nullable=True))
        batch_op.alter_column('tour_id', existing_type=sa.INTEGER(), nullable=True)
        batch_op.alter_column('departure_id', existing_type=sa.INTEGER(), nullable=True)
        batch_op.create_index(batch_op.f('ix_bookings_booking_type'), ['booking_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_bookings_service_id'), ['service_id'], unique=False)
        batch_op.create_foreign_key(
            'fk_bookings_service_id_services',
            'services',
            ['service_id'],
            ['id'],
        )

    with op.batch_alter_table('services', schema=None) as batch_op:
        batch_op.add_column(sa.Column('overview', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('highlights', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('what_is_included', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('how_it_works', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('who_its_for', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('important_notes', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('hero_image', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('seo_title', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('seo_description', sa.String(length=320), nullable=True))
        batch_op.add_column(
            sa.Column('is_bookable', sa.Boolean(), nullable=False, server_default=sa.true())
        )


def downgrade():
    with op.batch_alter_table('services', schema=None) as batch_op:
        batch_op.drop_column('is_bookable')
        batch_op.drop_column('seo_description')
        batch_op.drop_column('seo_title')
        batch_op.drop_column('hero_image')
        batch_op.drop_column('important_notes')
        batch_op.drop_column('who_its_for')
        batch_op.drop_column('how_it_works')
        batch_op.drop_column('what_is_included')
        batch_op.drop_column('highlights')
        batch_op.drop_column('overview')

    with op.batch_alter_table('bookings', schema=None) as batch_op:
        batch_op.drop_constraint('fk_bookings_service_id_services', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_bookings_service_id'))
        batch_op.drop_index(batch_op.f('ix_bookings_booking_type'))
        batch_op.alter_column('departure_id', existing_type=sa.INTEGER(), nullable=False)
        batch_op.alter_column('tour_id', existing_type=sa.INTEGER(), nullable=False)
        batch_op.drop_column('destination_country')
        batch_op.drop_column('preferred_travel_date')
        batch_op.drop_column('service_id')
        batch_op.drop_column('booking_type')
