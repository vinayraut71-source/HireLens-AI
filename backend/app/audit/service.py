"""Audit module — service layer."""
from sqlalchemy.ext.asyncio import AsyncSession
class AuditService:
    def __init__(self, db: AsyncSession): self.db = db
    async def log_action(self, user_id, agent_name, action_type, input_ref_type=None, input_ref_id=None, output_ref_type=None, output_ref_id=None, approval_status="not_required", metadata=None) -> dict: raise NotImplementedError("Sprint 1")
    async def list_logs(self, user_id, agent_name=None, action_type=None) -> list: raise NotImplementedError("Sprint 1")
