"""Add analytics_snapshots and analytics_insights tables

Revision ID: 0008_add_analytics_snapshots
Revises: 0007_add_job_applications
Create Date: 2026-06-15 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0008_add_analytics_snapshots'
down_revision: Union[str, None] = '0007_add_job_applications'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the analytics_snapshots table
    op.create_table(
        'analytics_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('total_applications', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_interviews', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_offers', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_rejections', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_acceptances', sa.Integer(), server_default='0', nullable=False),
        sa.Column('response_rate', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('interview_rate', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('offer_rate', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('acceptance_rate', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('average_ats_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('average_match_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('strongest_resume_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resume_versions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('ats_score_delta', sa.Float(), nullable=True),
        sa.Column('match_score_delta', sa.Float(), nullable=True),
        sa.Column('application_rate_delta', sa.Float(), nullable=True),
        sa.Column('interview_rate_delta', sa.Float(), nullable=True),
        sa.Column('funnel_stage_counts', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes for analytics_snapshots
    op.create_index('ix_analytics_snapshots_user_id', 'analytics_snapshots', ['user_id'], unique=False)

    # Create the analytics_insights table
    op.create_table(
        'analytics_insights',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('snapshot_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('analytics_snapshots.id', ondelete='CASCADE'), nullable=False),
        sa.Column('insight_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('impact_score', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes for analytics_insights
    op.create_index('ix_analytics_insights_snapshot_id', 'analytics_insights', ['snapshot_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_analytics_insights_snapshot_id', table_name='analytics_insights')
    op.drop_table('analytics_insights')

    op.drop_index('ix_analytics_snapshots_user_id', table_name='analytics_snapshots')
    op.drop_table('analytics_snapshots')
