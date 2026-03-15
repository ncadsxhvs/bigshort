"""Agent protocol / base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from bigshort.core.bus import EventBus


class Agent(ABC):
    """Base class for all agents."""

    name: str = "unnamed"

    @abstractmethod
    async def start(self, bus: EventBus) -> None:
        """Subscribe to topics and run the event loop."""

    async def stop(self) -> None:
        """Graceful shutdown (override if cleanup needed)."""

    def run_batch(self, data: dict[str, Any]) -> Any:
        """Synchronous research-mode entry point."""
        raise NotImplementedError(f"{self.name} does not support batch mode")
