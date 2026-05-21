"""add scraping schedule config

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-05-20
"""
from alembic import op
import sqlalchemy as sa

revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'scraping_schedule_config',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('interval_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('source', sa.String(20), nullable=False, server_default='all'),
        sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('scraping_schedule_config')
