"""resume_tailoring_audit

Revision ID: 0017_resume_tailoring_audit
Revises: 0016_add_resume_tailoring
Create Date: 2026-06-16 19:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0017_resume_tailoring_audit'
down_revision: Union[str, None] = '0016_add_resume_tailoring'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns to resume_tailoring_sessions
    op.add_column('resume_tailoring_sessions', sa.Column('tailoring_quality_score', sa.Integer(), nullable=True))
    op.add_column('resume_tailoring_sessions', sa.Column('resume_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    # Add unique constraint to resume_tailoring_sessions
    op.create_unique_constraint(
        'uq_resume_tailoring_sessions_version_hash_mode',
        'resume_tailoring_sessions',
        ['resume_version_id', 'job_description_hash', 'tailoring_mode']
    )
    
    # Add column to tailored_resume_suggestions
    op.add_column('tailored_resume_suggestions', sa.Column('severity_level', sa.String(length=20), nullable=True))


def downgrade() -> None:
    # Drop column from tailored_resume_suggestions
    op.drop_column('tailored_resume_suggestions', 'severity_level')
    
    # Drop unique constraint from resume_tailoring_sessions
    op.drop_constraint(
        'uq_resume_tailoring_sessions_version_hash_mode',
        'resume_tailoring_sessions',
        type_='unique'
    )
    
    # Drop columns from resume_tailoring_sessions
    op.drop_column('resume_tailoring_sessions', 'resume_snapshot')
    op.drop_column('resume_tailoring_sessions', 'tailoring_quality_score')
