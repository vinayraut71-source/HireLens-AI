"""Add resume parsing fields

Revision ID: 0002_add_resume_parsing_fields
Revises: 0001_initial_migration
Create Date: 2026-06-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0002_add_resume_parsing_fields'
down_revision: Union[str, None] = '0001_initial_migration'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('resume_versions', sa.Column('contact_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('resume_versions', sa.Column('education', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('resume_versions', sa.Column('experience', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('resume_versions', sa.Column('skills', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('resume_versions', sa.Column('certifications', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    op.create_index('ix_resume_versions_skills', 'resume_versions', ['skills'], unique=False, postgresql_using='gin')
    op.create_index('ix_resume_versions_contact_info', 'resume_versions', ['contact_info'], unique=False, postgresql_using='gin')


def downgrade() -> None:
    op.drop_index('ix_resume_versions_contact_info', table_name='resume_versions')
    op.drop_index('ix_resume_versions_skills', table_name='resume_versions')

    op.drop_column('resume_versions', 'certifications')
    op.drop_column('resume_versions', 'skills')
    op.drop_column('resume_versions', 'experience')
    op.drop_column('resume_versions', 'education')
    op.drop_column('resume_versions', 'contact_info')
