"""
Audit module — models.
PRD Section 7.2: agent_audit_log.
"""
import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import BaseModel


class AgentAuditLog(BaseModel):
    """Immutable audit trail for all AI Agent actions and Human-in-the-loop decisions. PRD Section 7.2, 10.4."""

    __tablename__ = "agent_audit_log"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    input_ref_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    input_ref_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    output_ref_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    output_ref_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    approval_status: Mapped[str] = mapped_column(String(20), default="not_required", server_default="not_required")
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, server_default="{}")
