"""Infrastructure module — service layer."""
from sqlalchemy.ext.asyncio import AsyncSession
class InfrastructureService:
    def __init__(self, db: AsyncSession): self.db = db
    async def check_health(self) -> dict: raise NotImplementedError("Sprint 0")
    async def get_config(self, service_name: str) -> dict: raise NotImplementedError("Sprint 0")
