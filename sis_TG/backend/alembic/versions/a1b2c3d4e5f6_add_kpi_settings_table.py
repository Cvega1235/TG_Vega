"""add kpi_settings table

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-06-06
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'kpi_settings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('revenue_green', sa.Numeric(12, 2), nullable=False),
        sa.Column('revenue_yellow', sa.Numeric(12, 2), nullable=False),
        sa.Column('clients_green', sa.Integer(), nullable=False),
        sa.Column('clients_yellow', sa.Integer(), nullable=False),
        sa.Column('new_clients_green', sa.Integer(), nullable=False),
        sa.Column('new_clients_yellow', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    # Insert default row
    op.execute(
        "INSERT INTO kpi_settings (revenue_green, revenue_yellow, clients_green, clients_yellow, "
        "new_clients_green, new_clients_yellow, updated_at) "
        "VALUES (150000, 75000, 30, 15, 5, 2, NOW())"
    )


def downgrade() -> None:
    op.drop_table('kpi_settings')
