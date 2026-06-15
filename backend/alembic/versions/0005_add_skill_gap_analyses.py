"""Add skill_gap_analyses table

Revision ID: 0005_add_skill_gap_analyses
Revises: 0004_add_job_matches
Create Date: 2026-06-15 13:07:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0005_add_skill_gap_analyses'
down_revision: Union[str, None] = '0004_add_job_matches'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the skill_gap_analyses table
    op.create_table(
        'skill_gap_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('resume_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resume_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_match_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_matches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('missing_skill', sa.String(length=255), nullable=False),
        sa.Column('importance_score', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('learning_priority', sa.String(length=20), nullable=False),
        sa.Column('estimated_learning_time', sa.String(length=100), nullable=False),
        sa.Column('recommendation_reason', sa.Text(), nullable=False),
        sa.Column('roadmap_priority_score', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes
    op.create_index('ix_skill_gap_analyses_user_id', 'skill_gap_analyses', ['user_id'], unique=False)
    op.create_index('ix_skill_gap_analyses_resume_version_id', 'skill_gap_analyses', ['resume_version_id'], unique=False)
    op.create_index('ix_skill_gap_analyses_job_match_id', 'skill_gap_analyses', ['job_match_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_skill_gap_analyses_job_match_id', table_name='skill_gap_analyses')
    op.drop_index('ix_skill_gap_analyses_resume_version_id', table_name='skill_gap_analyses')
    op.drop_index('ix_skill_gap_analyses_user_id', table_name='skill_gap_analyses')
    op.drop_table('skill_gap_analyses')
