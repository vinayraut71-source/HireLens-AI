"""Audit module — schemas. PRD Section 10.4."""
from uuid import UUID
from pydantic import BaseModel

class AuditLogResponse(BaseModel):
    id: UUID
    agent_name: str
    action_type: str
    input_ref_type: str | None = None
    input_ref_id: UUID | None = None
    output_ref_type: str | None = None
    output_ref_id: UUID | None = None
    approval_status: str
    metadata: dict = {}
    created_at: str | None = None
    class Config: from_attributes = True
