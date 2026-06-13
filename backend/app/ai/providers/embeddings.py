"""Gemini Embeddings client interface."""

class GeminiEmbeddings:
    """Generates dense vector representations using Gemini API. Scaffolding only."""
    def __init__(self):
        pass

    async def get_embedding(self, text: str) -> list[float]:
        raise NotImplementedError("Sprint 2")
