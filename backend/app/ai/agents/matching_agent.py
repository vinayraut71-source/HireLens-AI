"""MatchingAgent for vector matching."""
from app.ai.agents.base import BaseAgent
class MatchingAgent(BaseAgent):
    def __init__(self): super().__init__("MatchingAgent")
    async def run(self, resume_vector: list[float], job_vector: list[float]) -> dict: raise NotImplementedError("Sprint 4")
