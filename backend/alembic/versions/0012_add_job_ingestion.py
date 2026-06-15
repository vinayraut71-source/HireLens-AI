"""add_job_ingestion

Revision ID: 0012_add_job_ingestion
Revises: 0011_add_job_recommendations
Create Date: 2026-06-16 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0012_add_job_ingestion'
down_revision: Union[str, None] = '0011_add_job_recommendations'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Alter jobs.user_id to be nullable
    op.alter_column('jobs', 'user_id', existing_type=postgresql.UUID(as_uuid=True), nullable=True)

    # 2. Add columns to jobs table
    op.add_column('jobs', sa.Column('external_source', sa.String(length=50), nullable=True))
    op.add_column('jobs', sa.Column('external_job_id', sa.String(length=255), nullable=True))
    op.add_column('jobs', sa.Column('normalized_company', sa.String(length=255), nullable=True))
    op.add_column('jobs', sa.Column('normalized_location', sa.String(length=255), nullable=True))
    op.add_column('jobs', sa.Column('ingestion_hash', sa.String(length=64), nullable=True))
    op.add_column('jobs', sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('jobs', sa.Column('job_status', sa.String(length=20), nullable=False, server_default='active'))
    op.add_column('jobs', sa.Column('job_type', sa.String(length=50), nullable=True))
    op.add_column('jobs', sa.Column('experience_level', sa.String(length=50), nullable=True))

    # 3. Create indexes on jobs table
    op.create_index('ix_jobs_external_source', 'jobs', ['external_source'], unique=False)
    op.create_index('ix_jobs_external_job_id', 'jobs', ['external_job_id'], unique=False)
    op.create_index('ix_jobs_ingestion_hash', 'jobs', ['ingestion_hash'], unique=False)

    # 4. Add is_admin to users table
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))

    # 5. Create external_job_sources table
    op.create_table(
        'external_job_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_name', sa.String(length=50), nullable=False),
        sa.Column('source_job_id', sa.String(length=255), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    # Create indexes and unique constraint on external_job_sources
    op.create_index('ix_external_job_sources_source_name', 'external_job_sources', ['source_name'], unique=False)
    op.create_index('ix_external_job_sources_source_job_id', 'external_job_sources', ['source_job_id'], unique=False)
    op.create_index('ix_external_job_sources_source_name_job_id', 'external_job_sources', ['source_name', 'source_job_id'], unique=False)
    op.create_unique_constraint('uq_external_job_sources_source_name_job_id', 'external_job_sources', ['source_name', 'source_job_id'])


def downgrade() -> None:
    # 1. Drop external_job_sources table
    op.drop_table('external_job_sources')

    # 2. Drop is_admin from users table
    op.drop_column('users', 'is_admin')

    # 3. Drop indexes from jobs table
    op.drop_index('ix_jobs_ingestion_hash', table_name='jobs')
    op.drop_index('ix_jobs_external_job_id', table_name='jobs')
    op.drop_index('ix_jobs_external_source', table_name='jobs')

    # 4. Drop columns from jobs table
    op.drop_column('jobs', 'experience_level')
    op.drop_column('jobs', 'job_type')
    op.drop_column('jobs', 'job_status')
    op.drop_column('jobs', 'last_seen_at')
    op.drop_column('jobs', 'ingestion_hash')
    op.drop_column('jobs', 'normalized_location')
    op.drop_column('jobs', 'normalized_company')
    op.drop_column('jobs', 'external_job_id')
    op.drop_column('jobs', 'external_source')

    # 5. Alter jobs.user_id to be non-nullable (or keep it nullable as default downgrade fallback)
    op.alter_column('jobs', 'user_id', existing_type=postgresql.UUID(as_uuid=True), nullable=False)
