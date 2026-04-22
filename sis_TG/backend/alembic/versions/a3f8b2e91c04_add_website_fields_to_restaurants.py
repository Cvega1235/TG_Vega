"""add website fields to restaurants

Revision ID: a3f8b2e91c04
Revises: c7e4f9a12b35
Create Date: 2026-04-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3f8b2e91c04'
down_revision: Union[str, None] = 'c7e4f9a12b35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('restaurants', sa.Column('website_url', sa.Text(), nullable=True))
    op.add_column('restaurants', sa.Column('website_texto', sa.Text(), nullable=True))
    op.add_column('restaurants', sa.Column('website_scrapeado_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('restaurants', 'website_scrapeado_at')
    op.drop_column('restaurants', 'website_texto')
    op.drop_column('restaurants', 'website_url')
