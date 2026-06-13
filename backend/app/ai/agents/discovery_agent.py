"""DiscoveryAgent for job search and recommendation alerts."""
from app.ai.agents.base import BaseAgent
class DiscoveryAgent(BaseAgent):
    def __init__(self): super().__init__("DiscoveryAgent")
    async def run(self, user_preferences: dict) -> list: raise NotImplementedError("Sprint 4")
