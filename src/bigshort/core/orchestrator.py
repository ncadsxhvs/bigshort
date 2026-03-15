"""Orchestrator: runs agents in research (batch) or live (async) mode."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from bigshort.core.agent import Agent
from bigshort.core.bus import EventBus

logger = logging.getLogger(__name__)


def run_research(agents: list[Agent], data: dict[str, Any]) -> dict[str, Any]:
    """Run agents sequentially in batch mode (no asyncio)."""
    results: dict[str, Any] = {}
    for agent in agents:
        logger.info("batch: %s", agent.name)
        results[agent.name] = agent.run_batch(data)
        data.update(results)
    return results


async def run_live(agents: list[Agent], bus: EventBus) -> None:
    """Start all agents as concurrent asyncio tasks."""
    tasks = []
    for agent in agents:
        logger.info("starting: %s", agent.name)
        tasks.append(asyncio.create_task(agent.start(bus), name=agent.name))

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.info("shutting down agents")
    finally:
        for agent in agents:
            await agent.stop()
        bus.clear()
