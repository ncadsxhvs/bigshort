"""In-process asyncio EventBus (pub/sub)."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

from bigshort.core.events import Event

logger = logging.getLogger(__name__)


class EventBus:
    """Simple topic-based pub/sub backed by asyncio queues."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue[Event]]] = defaultdict(list)

    def subscribe(self, topic: str) -> asyncio.Queue[Event]:
        """Return a queue that receives all events published to *topic*."""
        q: asyncio.Queue[Event] = asyncio.Queue()
        self._subscribers[topic].append(q)
        return q

    async def publish(self, topic: str, event: Event) -> None:
        """Publish *event* to all subscribers of *topic*."""
        for q in self._subscribers[topic]:
            await q.put(event)
        logger.debug("published %s → %s", topic, type(event).__name__)

    def clear(self) -> None:
        """Remove all subscriptions."""
        self._subscribers.clear()
