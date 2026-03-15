"""Tests for the EventBus."""

from __future__ import annotations

import asyncio

import pytest

from bigshort.core.bus import EventBus
from bigshort.core.events import Event


@pytest.mark.asyncio
async def test_publish_subscribe():
    bus = EventBus()
    q = bus.subscribe("test.topic")
    event = Event(source="unit-test")
    await bus.publish("test.topic", event)
    received = await asyncio.wait_for(q.get(), timeout=1.0)
    assert received.source == "unit-test"


@pytest.mark.asyncio
async def test_multiple_subscribers():
    bus = EventBus()
    q1 = bus.subscribe("t")
    q2 = bus.subscribe("t")
    await bus.publish("t", Event(source="x"))
    assert (await q1.get()).source == "x"
    assert (await q2.get()).source == "x"


@pytest.mark.asyncio
async def test_no_crosstalk():
    bus = EventBus()
    q1 = bus.subscribe("a")
    q2 = bus.subscribe("b")
    await bus.publish("a", Event(source="a"))
    assert not q2.empty()  is False or q2.qsize() == 0


def test_clear():
    bus = EventBus()
    bus.subscribe("x")
    bus.clear()
    assert len(bus._subscribers) == 0
