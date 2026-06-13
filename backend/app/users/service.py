"""Users module — service layer."""
from sqlalchemy.ext.asyncio import AsyncSession

class UserService:
    def __init__(self, db: AsyncSession): self.db = db
    async def get_profile(self, user_id) -> dict: raise NotImplementedError("Sprint 1")
    async def update_profile(self, user_id, data) -> dict: raise NotImplementedError("Sprint 1")
    async def get_preferences(self, user_id) -> dict: raise NotImplementedError("Sprint 1")
    async def update_preferences(self, user_id, data) -> dict: raise NotImplementedError("Sprint 1")
    async def get_dashboard(self, user_id) -> dict: raise NotImplementedError("Sprint 6")
