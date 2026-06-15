"""Update recommendation_signals table

Revision ID: 0009_update_recommendation_signals
Revises: 0008_add_analytics_snapshots
Create Date: 2026-06-15 19:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0009_update_recommendation_signals'
down_revision: Union[str, None] = '0008_add_analytics_snapshots'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add new columns with defaults or nullable
    op.add_column('recommendation_signals', sa.Column('application_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_applications.id', ondelete='SET NULL'), nullable=True))
    op.add_column('recommendation_signals', sa.Column('resume_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resume_versions.id', ondelete='SET NULL'), nullable=True))
    op.add_column('recommendation_signals', sa.Column('job_match_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_matches.id', ondelete='SET NULL'), nullable=True))
    
    op.add_column('recommendation_signals', sa.Column('signal_source', sa.String(length=50), nullable=False, server_default='application'))
    op.add_column('recommendation_signals', sa.Column('signal_value', sa.Float(), nullable=False, server_default=1.0))
    op.add_column('recommendation_signals', sa.Column('confidence_score', sa.Float(), nullable=False, server_default=1.0))
    op.add_column('recommendation_signals', sa.Column('signal_weight', sa.Float(), nullable=False, server_default=1.0))
    op.add_column('recommendation_signals', sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}'))

    # 2. Alter existing columns (increase length of signal_type)
    op.alter_column('recommendation_signals', 'signal_type', type_=sa.String(length=50), existing_type=sa.String(length=30))

    # 3. Migrate data from legacy columns to new columns
    op.execute("UPDATE recommendation_signals SET signal_weight = weight, signal_value = weight")

    # 4. Remove server defaults to match target schema exactly
    op.alter_column('recommendation_signals', 'signal_source', server_default=None)
    op.alter_column('recommendation_signals', 'signal_value', server_default=None)
    op.alter_column('recommendation_signals', 'confidence_score', server_default=None)
    op.alter_column('recommendation_signals', 'signal_weight', server_default=None)
    op.alter_column('recommendation_signals', 'metadata', server_default=None)

    # 5. Drop legacy columns
    op.drop_column('recommendation_signals', 'signal_key')
    op.drop_column('recommendation_signals', 'weight')
    op.drop_column('recommendation_signals', 'sample_count')

    # 6. Create index on user_id
    op.create_index('ix_recommendation_signals_user_id', 'recommendation_signals', ['user_id'], unique=False)


def downgrade() -> None:
    # 1. Drop index
    op.drop_index('ix_recommendation_signals_user_id', table_name='recommendation_signals')

    # 2. Re-add legacy columns with server defaults for existing rows
    op.add_column('recommendation_signals', sa.Column('signal_key', sa.String(length=255), nullable=False, server_default='legacy_signal'))
    op.add_column('recommendation_signals', sa.Column('weight', sa.Float(), nullable=False, server_default=1.0))
    op.add_column('recommendation_signals', sa.Column('sample_count', sa.Integer(), nullable=False, server_default=1))

    # 3. Migrate data back from signal_weight to weight
    op.execute("UPDATE recommendation_signals SET weight = signal_weight")

    # 4. Remove server defaults
    op.alter_column('recommendation_signals', 'signal_key', server_default=None)
    op.alter_column('recommendation_signals', 'weight', server_default=None)
    op.alter_column('recommendation_signals', 'sample_count', server_default=None)

    # 5. Alter signal_type back to String(30)
    op.alter_column('recommendation_signals', 'signal_type', type_=sa.String(length=30), existing_type=sa.String(length=50))

    # 6. Drop the new columns
    op.drop_column('recommendation_signals', 'application_id')
    op.drop_column('recommendation_signals', 'resume_version_id')
    op.drop_column('recommendation_signals', 'job_match_id')
    op.drop_column('recommendation_signals', 'signal_source')
    op.drop_column('recommendation_signals', 'signal_value')
    op.drop_column('recommendation_signals', 'confidence_score')
    op.drop_column('recommendation_signals', 'signal_weight')
    op.drop_column('recommendation_signals', 'metadata')
