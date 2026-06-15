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
    # Drop the legacy table
    op.drop_table('recommendation_signals')

    # Recreate the table with new columns
    op.create_table(
        'recommendation_signals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_applications.id', ondelete='SET NULL'), nullable=True),
        sa.Column('resume_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resume_versions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('job_match_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_matches.id', ondelete='SET NULL'), nullable=True),
        sa.Column('signal_type', sa.String(length=50), nullable=False),
        sa.Column('signal_source', sa.String(length=50), nullable=False),
        sa.Column('signal_value', sa.Float(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('signal_weight', sa.Float(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create index
    op.create_index('ix_recommendation_signals_user_id', 'recommendation_signals', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_recommendation_signals_user_id', table_name='recommendation_signals')
    op.drop_table('recommendation_signals')

    # Recreate legacy table
    op.create_table(
        'recommendation_signals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('signal_type', sa.String(length=30), nullable=False),
        sa.Column('signal_key', sa.String(length=255), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False),
        sa.Column('sample_count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
