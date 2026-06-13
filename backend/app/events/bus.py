"""
Event Bus Interface.
Defines contracts for publishing and subscribing to system-wide domain events.
"""
from typing import Any, Callable, Coroutine

class EventBus:
    """Interface for asynchronous publish-subscribe message distribution."""
    
    async def publish(self, topic: str, event_data: Any) -> None:
        """Publish an event to a specific topic."""
        raise NotImplementedError()
        
    async def subscribe(self, topic: str, handler: Callable[[Any], Coroutine[Any, Any, None]]) -> None:
        """Subscribe a handler function to a topic."""
        raise NotImplementedError()
