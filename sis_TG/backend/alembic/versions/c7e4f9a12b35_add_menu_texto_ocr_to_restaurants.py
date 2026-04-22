"""add menu_texto_ocr to restaurants

Revision ID: c7e4f9a12b35
Revises: 58a9c3bc35f2
Create Date: 2026-04-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c7e4f9a12b35'
down_revision: Union[str, None] = '58a9c3bc35f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('restaurants', sa.Column('menu_texto_ocr', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('restaurants', 'menu_texto_ocr')
