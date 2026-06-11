"""add max_clients to kpi_settings

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-08
"""
from alembic import op
import sqlalchemy as sa

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # DEFAULT 72 rellena la fila existente (29 clientes / 0.40 capacidad actual ≈ 72)
    op.add_column(
        'kpi_settings',
        sa.Column('max_clients', sa.Integer(), nullable=False, server_default='72'),
    )


def downgrade() -> None:
    op.drop_column('kpi_settings', 'max_clients')
