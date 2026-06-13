"""CoachingAgent for skill gap identification and roadmaps."""
from app.ai.agents.base import BaseAgent
class CoachingAgent(BaseAgent):
    def __init__(self): super().__init__("CoachingAgent")
    async def run(self, match_result: dict) -> dict: raise NotImplementedError("Sprint 5")
