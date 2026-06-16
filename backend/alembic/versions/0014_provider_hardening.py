"""provider_hardening

Revision ID: 0014_provider_hardening
Revises: 0013_add_provider_sync_logs
Create Date: 2026-06-16 04:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0014_provider_hardening'
down_revision: Union[str, None] = '0013_add_provider_sync_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add columns to provider_sync_logs
    op.add_column('provider_sync_logs', sa.Column('records_processed', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('provider_sync_logs', sa.Column('execution_duration_ms', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('provider_sync_logs', sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))

    # 2. Create provider_configs table
    op.create_table(
        'provider_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('provider_name', sa.String(length=50), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sync_interval_minutes', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('rate_limit_per_hour', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('retry_limit', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('timeout_seconds', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_provider_configs_provider_name', 'provider_configs', ['provider_name'], unique=True)

    # 3. Create provider_locks table
    op.create_table(
        'provider_locks',
        sa.Column('provider_name', sa.String(length=50), primary_key=True),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=False),
        sa.Column('locked_by', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )

    # 4. Create failed_sync_jobs table
    op.create_table(
        'failed_sync_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('provider_name', sa.String(length=50), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_failed_sync_jobs_provider_name', 'failed_sync_jobs', ['provider_name'], unique=False)

    # 5. Create provider_toggle_audits table
    op.create_table(
        'provider_toggle_audits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('admin_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_name', sa.String(length=50), nullable=False),
        sa.Column('old_state', sa.Boolean(), nullable=False),
        sa.Column('new_state', sa.Boolean(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['admin_user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('ix_provider_toggle_audits_admin_user_id', 'provider_toggle_audits', ['admin_user_id'], unique=False)
    op.create_index('ix_provider_toggle_audits_provider_name', 'provider_toggle_audits', ['provider_name'], unique=False)


def downgrade() -> None:
    # Drop indexes and tables
    op.drop_index('ix_provider_toggle_audits_provider_name', table_name='provider_toggle_audits')
    op.drop_index('ix_provider_toggle_audits_admin_user_id', table_name='provider_toggle_audits')
    op.drop_table('provider_toggle_audits')

    op.drop_index('ix_failed_sync_jobs_provider_name', table_name='failed_sync_jobs')
    op.drop_table('failed_sync_jobs')

    op.drop_table('provider_locks')

    op.drop_index('ix_provider_configs_provider_name', table_name='provider_configs')
    op.drop_table('provider_configs')

    # Drop columns from provider_sync_logs
    op.drop_column('provider_sync_logs', 'retry_count')
    op.drop_column('provider_sync_logs', 'execution_duration_ms')
    op.drop_column('provider_sync_logs', 'records_processed')
