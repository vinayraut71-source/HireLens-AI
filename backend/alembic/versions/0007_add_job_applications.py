"""Add job_applications and application_timeline_events tables

Revision ID: 0007_add_job_applications
Revises: 0006_add_career_roadmaps
Create Date: 2026-06-15 13:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0007_add_job_applications'
down_revision: Union[str, None] = '0006_add_career_roadmaps'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the job_applications table
    op.create_table(
        'job_applications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('resume_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resume_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(length=30), server_default='draft', nullable=False),
        sa.Column('outcome_type', sa.Enum('unknown', 'no_response', 'rejected', 'interviewed', 'offered', 'accepted', name='outcome_type_enum'), server_default='unknown', nullable=False),
        sa.Column('job_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('first_response_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('interview_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('offer_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes for job_applications
    op.create_index('ix_job_applications_user_id', 'job_applications', ['user_id'], unique=False)
    op.create_index('ix_job_applications_job_id', 'job_applications', ['job_id'], unique=False)
    op.create_index('ix_job_applications_resume_version_id', 'job_applications', ['resume_version_id'], unique=False)

    # Create the application_timeline_events table
    op.create_table(
        'application_timeline_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_applications.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('previous_status', sa.String(length=30), nullable=True),
        sa.Column('new_status', sa.String(length=30), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes for application_timeline_events
    op.create_index('ix_application_timeline_events_application_id', 'application_timeline_events', ['application_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_application_timeline_events_application_id', table_name='application_timeline_events')
    op.drop_table('application_timeline_events')

    op.drop_index('ix_job_applications_resume_version_id', table_name='job_applications')
    op.drop_index('ix_job_applications_job_id', table_name='job_applications')
    op.drop_index('ix_job_applications_user_id', table_name='job_applications')
    op.drop_table('job_applications')

    # Drop enum type on postgres if it exists
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        sa.Enum(name='outcome_type_enum').drop(bind)
