"""add classifier columns: conversion_probability and classification metrics

Revision ID: d4e5f6a7b8c9
Revises: b1e2f3a4c5d6
Create Date: 2026-05-19 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'd4e5f6a7b8c9'
down_revision = 'b1e2f3a4c5d6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Probabilidad de conversión por restaurante (clasificador supervisado)
    op.add_column(
        'restaurant_ml_scores',
        sa.Column('conversion_probability', sa.Numeric(5, 4), nullable=True),
    )

    # Métricas del clasificador supervisado en cada ejecución ML
    op.add_column('ml_run_metadata', sa.Column('cls_precision', sa.Numeric(5, 4), nullable=True))
    op.add_column('ml_run_metadata', sa.Column('cls_recall', sa.Numeric(5, 4), nullable=True))
    op.add_column('ml_run_metadata', sa.Column('cls_f1', sa.Numeric(5, 4), nullable=True))
    op.add_column('ml_run_metadata', sa.Column('cls_auc_roc', sa.Numeric(5, 4), nullable=True))
    op.add_column('ml_run_metadata', sa.Column('cls_cv_f1_mean', sa.Numeric(5, 4), nullable=True))
    op.add_column('ml_run_metadata', sa.Column('cls_cv_f1_std', sa.Numeric(5, 4), nullable=True))
    op.add_column('ml_run_metadata', sa.Column('cls_support_positive', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('restaurant_ml_scores', 'conversion_probability')
    op.drop_column('ml_run_metadata', 'cls_precision')
    op.drop_column('ml_run_metadata', 'cls_recall')
    op.drop_column('ml_run_metadata', 'cls_f1')
    op.drop_column('ml_run_metadata', 'cls_auc_roc')
    op.drop_column('ml_run_metadata', 'cls_cv_f1_mean')
    op.drop_column('ml_run_metadata', 'cls_cv_f1_std')
    op.drop_column('ml_run_metadata', 'cls_support_positive')
