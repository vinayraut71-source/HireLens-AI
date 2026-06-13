"""
Audit Event Contracts.
Contracts for security-critical actions and AI agent operation logs.
"""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass(frozen=True)
class AuditEvent:
    event_id: UUID
    timestamp: datetime
    user_id: UUID
    event_type: str

@dataclass(frozen=True)
class UserAuthAuditEvent(AuditEvent):
    action: str  # login, logout, password_reset
    ip_address: str
    user_agent: str

@dataclass(frozen=True)
class AgentExecutionAuditEvent(AuditEvent):
    agent_name: str
    action_type: str
    input_ref_id: UUID
    output_ref_id: UUID
    approval_status: str
