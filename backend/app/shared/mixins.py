"""
Shared mixins for domain-specific model patterns.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class UserOwnedMixin:
    """Mixin for models owned by a user (row-level security pattern)."""

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


class AuditableMixin:
    """Mixin for models that require audit trail metadata."""

    created_by: Mapped[str | None] = mapped_column(
        String(50), nullable=True, default=None
    )
    last_modified_by: Mapped[str | None] = mapped_column(
        String(50), nullable=True, default=None
    )


class VersionedMixin:
    """Mixin for models that support immutable version snapshots."""

    version_number: Mapped[int] = mapped_column(nullable=False)
    version_label: Mapped[str] = mapped_column(String(50), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    parent_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
