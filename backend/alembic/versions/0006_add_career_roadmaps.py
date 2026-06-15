"""Add career_roadmaps and roadmap_milestones tables

Revision ID: 0006_add_career_roadmaps
Revises: 0005_add_skill_gap_analyses
Create Date: 2026-06-15 13:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0006_add_career_roadmaps'
down_revision: Union[str, None] = '0005_add_skill_gap_analyses'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the career_roadmaps table
    op.create_table(
        'career_roadmaps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('resume_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resume_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_match_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_matches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('total_estimated_weeks', sa.Integer(), nullable=False),
        sa.Column('roadmap_status', sa.String(length=20), server_default='active', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes for career_roadmaps
    op.create_index('ix_career_roadmaps_user_id', 'career_roadmaps', ['user_id'], unique=False)
    op.create_index('ix_career_roadmaps_resume_version_id', 'career_roadmaps', ['resume_version_id'], unique=False)
    op.create_index('ix_career_roadmaps_job_match_id', 'career_roadmaps', ['job_match_id'], unique=False)

    # Create the roadmap_milestones table
    op.create_table(
        'roadmap_milestones',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('roadmap_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('career_roadmaps.id', ondelete='CASCADE'), nullable=False),
        sa.Column('skill_gap_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skill_gap_analyses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('milestone_order', sa.Integer(), nullable=False),
        sa.Column('milestone_title', sa.String(length=255), nullable=False),
        sa.Column('estimated_weeks', sa.Integer(), nullable=False),
        sa.Column('priority_score', sa.Integer(), nullable=False),
        sa.Column('completion_status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes for roadmap_milestones
    op.create_index('ix_roadmap_milestones_roadmap_id', 'roadmap_milestones', ['roadmap_id'], unique=False)
    op.create_index('ix_roadmap_milestones_skill_gap_id', 'roadmap_milestones', ['skill_gap_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_roadmap_milestones_skill_gap_id', table_name='roadmap_milestones')
    op.drop_index('ix_roadmap_milestones_roadmap_id', table_name='roadmap_milestones')
    op.drop_table('roadmap_milestones')

    op.drop_index('ix_career_roadmaps_job_match_id', table_name='career_roadmaps')
    op.drop_index('ix_career_roadmaps_resume_version_id', table_name='career_roadmaps')
    op.drop_index('ix_career_roadmaps_user_id', table_name='career_roadmaps')
    op.drop_table('career_roadmaps')
