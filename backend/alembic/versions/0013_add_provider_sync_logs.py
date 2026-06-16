"""add_provider_sync_logs

Revision ID: 0013_add_provider_sync_logs
Revises: 0012_add_job_ingestion
Create Date: 2026-06-16 03:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0013_add_provider_sync_logs'
down_revision: Union[str, None] = '0012_add_job_ingestion'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create provider_sync_logs table
    op.create_table(
        'provider_sync_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('provider_name', sa.String(length=50), nullable=False),
        sa.Column('sync_started_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('sync_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('jobs_received', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('jobs_created', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('jobs_updated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('jobs_expired', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )

    # Create indexes on provider_sync_logs
    op.create_index('ix_provider_sync_logs_provider_name', 'provider_sync_logs', ['provider_name'], unique=False)
    op.create_index('ix_provider_sync_logs_status', 'provider_sync_logs', ['status'], unique=False)
    op.create_index('ix_provider_sync_logs_sync_started_at', 'provider_sync_logs', ['sync_started_at'], unique=False)


def downgrade() -> None:
    # Drop indexes from provider_sync_logs
    op.drop_index('ix_provider_sync_logs_sync_started_at', table_name='provider_sync_logs')
    op.drop_index('ix_provider_sync_logs_status', table_name='provider_sync_logs')
    op.drop_index('ix_provider_sync_logs_provider_name', table_name='provider_sync_logs')

    # Drop provider_sync_logs table
    op.drop_table('provider_sync_logs')
