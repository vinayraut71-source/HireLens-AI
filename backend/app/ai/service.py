"""AI Layer — service layer."""
from sqlalchemy.ext.asyncio import AsyncSession
class AiService:
    def __init__(self, db: AsyncSession): self.db = db
    async def parse_resume(self, raw_text: str) -> dict: raise NotImplementedError("Sprint 2")
    async def score_ats(self, parsed_resume: dict, jd_text: str) -> dict: raise NotImplementedError("Sprint 3")
    async def generate_roadmap(self, skill_gaps: list) -> dict: raise NotImplementedError("Sprint 5")
