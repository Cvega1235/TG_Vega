"""add security tables: audit_logs and user lockout fields

Revision ID: b1e2f3a4c5d6
Revises: a3f8b2e91c04
Create Date: 2026-04-23 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'b1e2f3a4c5d6'
down_revision = 'a3f8b2e91c04'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Tabla audit_logs ──────────────────────────────────────────────────────
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_email', sa.String(length=255), nullable=True),
        sa.Column('action', sa.String(length=80), nullable=False),
        sa.Column('resource', sa.String(length=80), nullable=True),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='success'),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=300), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('ix_audit_logs_ip_address', 'audit_logs', ['ip_address'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])

    # ── Columnas de bloqueo en users ──────────────────────────────────────────
    op.add_column('users', sa.Column('failed_attempts', sa.Integer(), nullable=False,
                                     server_default='0'))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True))

    # ── Ampliar telefono en restaurants (cifrado puede superar 50 chars) ──────
    op.alter_column('restaurants', 'telefono',
                    existing_type=sa.String(length=50),
                    type_=sa.Text(),
                    existing_nullable=True)


def downgrade() -> None:
    op.alter_column('restaurants', 'telefono',
                    existing_type=sa.Text(),
                    type_=sa.String(length=50),
                    existing_nullable=True)

    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_attempts')

    op.drop_index('ix_audit_logs_user_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_ip_address', table_name='audit_logs')
    op.drop_index('ix_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('ix_audit_logs_action', table_name='audit_logs')
    op.drop_table('audit_logs')
