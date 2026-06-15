"""Add job_matches table

Revision ID: 0004_add_job_matches
Revises: 0003_add_ats_analyses
Create Date: 2026-06-15 12:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0004_add_job_matches'
down_revision: Union[str, None] = '0003_add_ats_analyses'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add soft-delete columns to jobs table (Sprint 5 enhancement)
    op.add_column('jobs', sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('jobs', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('jobs', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))

    # Create the job_matches table
    op.create_table(
        'job_matches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('resume_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resume_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('overall_match_score', sa.Float(), nullable=False),
        sa.Column('skills_match_score', sa.Float(), nullable=False),
        sa.Column('experience_match_score', sa.Float(), nullable=False),
        sa.Column('education_match_score', sa.Float(), nullable=False),
        sa.Column('keyword_match_score', sa.Float(), nullable=False),
        sa.Column('matched_skills', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('missing_skills', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('strengths', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('weaknesses', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('fit_summary', sa.Text(), nullable=False, server_default=''),
        sa.Column('improvement_actions', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes
    op.create_index('ix_job_matches_user_id', 'job_matches', ['user_id'], unique=False)
    op.create_index('ix_job_matches_resume_version_id', 'job_matches', ['resume_version_id'], unique=False)
    op.create_index('ix_job_matches_job_id', 'job_matches', ['job_id'], unique=False)
    op.create_index('ix_job_matches_user_job_version', 'job_matches', ['user_id', 'job_id', 'resume_version_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_job_matches_user_job_version', table_name='job_matches')
    op.drop_index('ix_job_matches_job_id', table_name='job_matches')
    op.drop_index('ix_job_matches_resume_version_id', table_name='job_matches')
    op.drop_index('ix_job_matches_user_id', table_name='job_matches')
    op.drop_table('job_matches')

    op.drop_column('jobs', 'updated_at')
    op.drop_column('jobs', 'deleted_at')
    op.drop_column('jobs', 'is_deleted')
