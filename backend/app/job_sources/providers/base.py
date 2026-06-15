from abc import ABC, abstractmethod

class BaseJobProvider(ABC):
    @abstractmethod
    async def fetch_jobs(self) -> list[dict]:
        """Fetch raw/source jobs. Returns list of dicts."""
        pass
