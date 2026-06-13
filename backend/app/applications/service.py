"""Applications module — service layer."""
from sqlalchemy.ext.asyncio import AsyncSession
class ApplicationService:
    def __init__(self, db: AsyncSession): self.db = db
    async def create(self, user_id, data) -> dict: raise NotImplementedError("Sprint 6")
    async def list_all(self, user_id, status=None) -> list: raise NotImplementedError("Sprint 6")
    async def get(self, user_id, app_id) -> dict: raise NotImplementedError("Sprint 6")
    async def update(self, user_id, app_id, data) -> dict: raise NotImplementedError("Sprint 6")
    async def delete(self, user_id, app_id) -> None: raise NotImplementedError("Sprint 6")
    async def get_stats(self, user_id) -> dict: raise NotImplementedError("Sprint 6")
    async def record_outcome(self, user_id, app_id, event_type, metadata=None) -> dict: raise NotImplementedError("Sprint 6")
    async def list_outcomes(self, user_id, app_id) -> list: raise NotImplementedError("Sprint 6")

class PackageService:
    def __init__(self, db: AsyncSession): self.db = db
    async def create_package(self, user_id, job_id) -> dict: raise NotImplementedError("Phase 2")
    async def list_packages(self, user_id) -> list: raise NotImplementedError("Phase 2")
    async def get_package(self, user_id, pkg_id) -> dict: raise NotImplementedError("Phase 2")
    async def approve(self, user_id, pkg_id) -> dict: raise NotImplementedError("Phase 2")
    async def reject(self, user_id, pkg_id) -> dict: raise NotImplementedError("Phase 2")
    async def submit(self, user_id, pkg_id) -> dict: raise NotImplementedError("Phase 2")
