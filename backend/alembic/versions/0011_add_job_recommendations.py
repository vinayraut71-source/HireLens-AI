"""add_job_recommendations

Revision ID: 0011_add_job_recommendations
Revises: 0010_add_password_reset_tokens
Create Date: 2026-06-16 01:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0011_add_job_recommendations'
down_revision: Union[str, None] = '0010_add_password_reset_tokens'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'job_recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('resume_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resume_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('recommendation_score', sa.Float(), nullable=False),
        sa.Column('match_score', sa.Float(), nullable=False),
        sa.Column('ats_score', sa.Float(), nullable=False),
        sa.Column('skill_gap_score', sa.Float(), nullable=False),
        sa.Column('feedback_score', sa.Float(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('recommendation_reason', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('recommendation_status', sa.String(length=20), nullable=False, server_default='recommended'),
        sa.Column('job_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    # Create required indexes
    op.create_index('ix_job_recommendations_user_id', 'job_recommendations', ['user_id'], unique=False)
    op.create_index('ix_job_recommendations_job_id', 'job_recommendations', ['job_id'], unique=False)
    op.create_index('ix_job_recommendations_recommendation_score', 'job_recommendations', ['recommendation_score'], unique=False)
    op.create_index('ix_job_recommendations_recommendation_status', 'job_recommendations', ['recommendation_status'], unique=False)
    op.create_index('ix_job_recommendations_user_id_status', 'job_recommendations', ['user_id', 'recommendation_status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_job_recommendations_user_id_status', table_name='job_recommendations')
    op.drop_index('ix_job_recommendations_recommendation_status', table_name='job_recommendations')
    op.drop_index('ix_job_recommendations_recommendation_score', table_name='job_recommendations')
    op.drop_index('ix_job_recommendations_job_id', table_name='job_recommendations')
    op.drop_index('ix_job_recommendations_user_id', table_name='job_recommendations')
    op.drop_table('job_recommendations')

