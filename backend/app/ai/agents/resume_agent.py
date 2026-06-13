"""ResumeAgent for parsing, extraction and ATS scoring."""
from app.ai.agents.base import BaseAgent
class ResumeAgent(BaseAgent):
    def __init__(self): super().__init__("ResumeAgent")
    async def run(self, raw_text: str) -> dict: raise NotImplementedError("Sprint 2")
