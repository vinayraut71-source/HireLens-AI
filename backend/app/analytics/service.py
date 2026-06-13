"""Analytics module — service layer."""
from sqlalchemy.ext.asyncio import AsyncSession
class AnalyticsService:
    def __init__(self, db: AsyncSession): self.db = db
    async def get_latest_snapshot(self, user_id) -> dict: raise NotImplementedError("Sprint 6")
    async def get_timeseries(self, user_id, metric, start_date, end_date) -> list: raise NotImplementedError("Sprint 6")
    async def trigger_snapshot_generation(self, user_id) -> dict: raise NotImplementedError("Sprint 6")
