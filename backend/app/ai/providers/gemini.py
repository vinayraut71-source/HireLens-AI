"""Gemini API client interface."""

class GeminiClient:
    """Interface to interact with Gemini LLM models. Scaffolding only."""
    def __init__(self):
        pass

    async def generate_content(self, prompt: str, system_instruction: str = None) -> str:
        raise NotImplementedError("Sprint 2")
