"""provider_hardening_v2

Revision ID: 0015_provider_hardening_v2
Revises: 0014_provider_hardening
Create Date: 2026-06-16 05:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0015_provider_hardening_v2'
down_revision: Union[str, None] = '0014_provider_hardening'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update provider_configs
    op.add_column('provider_configs', sa.Column('max_concurrent_jobs', sa.Integer(), nullable=False, server_default='1'))

    # 2. Update provider_locks
    op.add_column('provider_locks', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))

    # 3. Update failed_sync_jobs
    op.add_column('failed_sync_jobs', sa.Column('resolved', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('failed_sync_jobs', sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True))

    # 4. Update provider_toggle_audits
    op.add_column('provider_toggle_audits', sa.Column('reason', sa.Text(), nullable=True))


def downgrade() -> None:
    # Drop added columns
    op.drop_column('provider_toggle_audits', 'reason')
    op.drop_column('failed_sync_jobs', 'resolved_at')
    op.drop_column('failed_sync_jobs', 'resolved')
    op.drop_column('provider_locks', 'created_at')
    op.drop_column('provider_configs', 'max_concurrent_jobs')
