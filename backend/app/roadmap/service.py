"""Roadmap module — service layer."""
from sqlalchemy.ext.asyncio import AsyncSession
class RoadmapService:
    def __init__(self, db: AsyncSession): self.db = db
    async def generate_roadmap(self, user_id, match_result_id, title=None) -> dict: raise NotImplementedError("Sprint 5")
    async def get_roadmap(self, user_id, roadmap_id) -> dict: raise NotImplementedError("Sprint 5")
    async def list_roadmaps(self, user_id) -> list: raise NotImplementedError("Sprint 5")
    async def update_module_status(self, user_id, roadmap_id, module_id, status) -> dict: raise NotImplementedError("Sprint 5")
