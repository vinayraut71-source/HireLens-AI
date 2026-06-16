import logging
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)


class EventBus:
    """Interface for asynchronous publish-subscribe message distribution."""
    
    async def publish(self, topic: str, event_data: Any) -> None:
        """Publish an event to a specific topic."""
        raise NotImplementedError()
        
    async def subscribe(self, topic: str, handler: Callable[[Any], Coroutine[Any, Any, None]]) -> None:
        """Subscribe a handler function to a topic."""
        raise NotImplementedError()


class DefaultEventBus(EventBus):
    def __init__(self):
        self.published_events = []

    async def publish(self, topic: str, event_data: Any) -> None:
        self.published_events.append((topic, event_data))
        logger.info(f"Published event on topic {topic}: {event_data}")

    async def subscribe(self, topic: str, handler: Callable[[Any], Coroutine[Any, Any, None]]) -> None:
        pass


event_bus = DefaultEventBus()

