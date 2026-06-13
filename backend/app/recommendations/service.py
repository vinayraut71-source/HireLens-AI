"""Recommendations module — service layer."""
from sqlalchemy.ext.asyncio import AsyncSession
class RecommendationService:
    def __init__(self, db: AsyncSession): self.db = db
    async def get_recommended_jobs(self, user_id, limit=10) -> list: raise NotImplementedError("Sprint 4")
    async def record_interaction(self, user_id, interaction_type, key, value) -> None: raise NotImplementedError("Sprint 4")
