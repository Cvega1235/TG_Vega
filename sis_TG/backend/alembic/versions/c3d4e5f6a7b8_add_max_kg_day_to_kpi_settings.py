"""add max_kg_day to kpi_settings

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-09
"""
from alembic import op
import sqlalchemy as sa

revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'kpi_settings',
        sa.Column('max_kg_day', sa.Numeric(8, 2), nullable=False, server_default='100'),
    )


def downgrade() -> None:
    op.drop_column('kpi_settings', 'max_kg_day')
