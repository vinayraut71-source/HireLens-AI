"""Jobs module — service layer."""
from sqlalchemy.ext.asyncio import AsyncSession
class JobService:
    def __init__(self, db: AsyncSession): self.db = db
    async def create_job(self, user_id, data) -> dict: raise NotImplementedError("Sprint 4")
    async def list_jobs(self, user_id) -> list: raise NotImplementedError("Sprint 4")
    async def get_job(self, user_id, job_id) -> dict: raise NotImplementedError("Sprint 4")
    async def update_job(self, user_id, job_id, data) -> dict: raise NotImplementedError("Sprint 4")
    async def delete_job(self, user_id, job_id) -> None: raise NotImplementedError("Sprint 4")
    async def match_resume(self, user_id, job_id, version_id) -> dict: raise NotImplementedError("Sprint 4")
    async def analyze_jd(self, user_id, jd_text) -> dict: raise NotImplementedError("Sprint 4")
