"""Add ats_analyses table

Revision ID: 0003_add_ats_analyses
Revises: 0002_add_resume_parsing_fields
Create Date: 2026-06-14 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0003_add_ats_analyses'
down_revision: Union[str, None] = '0002_add_resume_parsing_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ats_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('resume_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resume_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_description_hash', sa.String(length=64), nullable=False),
        sa.Column('ats_score', sa.Integer(), nullable=False),
        sa.Column('keyword_score', sa.Integer(), nullable=False),
        sa.Column('skills_score', sa.Integer(), nullable=False),
        sa.Column('experience_score', sa.Integer(), nullable=False),
        sa.Column('education_score', sa.Integer(), nullable=False),
        sa.Column('missing_keywords', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('matched_keywords', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('recommendations', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('matched_skills', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('missing_skills', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('resume_strengths', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('resume_weaknesses', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('matched_sections', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_ats_analyses_job_description_hash', 'ats_analyses', ['job_description_hash'], unique=False)
    op.create_index('ix_ats_analyses_resume_version_id', 'ats_analyses', ['resume_version_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_ats_analyses_resume_version_id', table_name='ats_analyses')
    op.drop_index('ix_ats_analyses_job_description_hash', table_name='ats_analyses')
    op.drop_table('ats_analyses')
