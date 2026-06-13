"""Base class for all AI agents."""
from typing import Any
class BaseAgent:
    """Abstract agent class declaring standard lifecycle methods."""
    def __init__(self, name: str):
        self.name = name
    async def run(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()
