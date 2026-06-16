"""add_resume_tailoring

Revision ID: 0016_add_resume_tailoring
Revises: 0015_provider_hardening_v2
Create Date: 2026-06-16 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0016_add_resume_tailoring'
down_revision: Union[str, None] = '0015_provider_hardening_v2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create resume_tailoring_sessions
    op.create_table(
        'resume_tailoring_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('resume_version_id', sa.UUID(), nullable=False),
        sa.Column('ats_analysis_id', sa.UUID(), nullable=True),
        sa.Column('job_match_id', sa.UUID(), nullable=True),
        sa.Column('job_title', sa.String(length=255), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=True),
        sa.Column('job_description_hash', sa.String(length=64), nullable=False),
        sa.Column('original_ats_score', sa.Integer(), nullable=False),
        sa.Column('tailored_ats_score', sa.Integer(), nullable=False),
        sa.Column('tailoring_mode', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_resume_tailoring_sessions_user_id_users'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resume_version_id'], ['resume_versions.id'], name=op.f('fk_resume_tailoring_sessions_resume_version_id_resume_versions'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ats_analysis_id'], ['ats_analyses.id'], name=op.f('fk_resume_tailoring_sessions_ats_analysis_id_ats_analyses'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['job_match_id'], ['job_matches.id'], name=op.f('fk_resume_tailoring_sessions_job_match_id_job_matches'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_resume_tailoring_sessions'))
    )
    op.create_index('ix_resume_tailoring_sessions_user_id', 'resume_tailoring_sessions', ['user_id'], unique=False)
    op.create_index('ix_resume_tailoring_sessions_resume_version_id', 'resume_tailoring_sessions', ['resume_version_id'], unique=False)
    op.create_index('ix_resume_tailoring_sessions_job_description_hash', 'resume_tailoring_sessions', ['job_description_hash'], unique=False)
    op.create_index('ix_resume_tailoring_sessions_status', 'resume_tailoring_sessions', ['status'], unique=False)

    # 2. Create tailored_resume_suggestions
    op.create_table(
        'tailored_resume_suggestions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('section_name', sa.String(length=30), nullable=False),
        sa.Column('suggestion_type', sa.String(length=30), nullable=False),
        sa.Column('original_content', sa.Text(), nullable=True),
        sa.Column('suggested_content', sa.Text(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['resume_tailoring_sessions.id'], name=op.f('fk_tailored_resume_suggestions_session_id_resume_tailoring_sessions'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_tailored_resume_suggestions'))
    )
    op.create_index('ix_tailored_resume_suggestions_session_id', 'tailored_resume_suggestions', ['session_id'], unique=False)
    op.create_index('ix_tailored_resume_suggestions_suggestion_type', 'tailored_resume_suggestions', ['suggestion_type'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_tailored_resume_suggestions_suggestion_type', table_name='tailored_resume_suggestions')
    op.drop_index('ix_tailored_resume_suggestions_session_id', table_name='tailored_resume_suggestions')
    op.drop_table('tailored_resume_suggestions')
    
    op.drop_index('ix_resume_tailoring_sessions_status', table_name='resume_tailoring_sessions')
    op.drop_index('ix_resume_tailoring_sessions_job_description_hash', table_name='resume_tailoring_sessions')
    op.drop_index('ix_resume_tailoring_sessions_resume_version_id', table_name='resume_tailoring_sessions')
    op.drop_index('ix_resume_tailoring_sessions_user_id', table_name='resume_tailoring_sessions')
    op.drop_table('resume_tailoring_sessions')
