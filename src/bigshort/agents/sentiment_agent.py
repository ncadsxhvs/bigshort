"""SentimentAgent — pulls news/reddit sentiment, emits SentimentEvent."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from bigshort.core.agent import Agent
from bigshort.core.bus import EventBus
from bigshort.core.events import SentimentEvent
from bigshort.sentiment.features import sentiment_delta

logger = logging.getLogger(__name__)


class SentimentAgent(Agent):
    name = "sentiment"

    def __init__(self, poll_interval: float = 900.0) -> None:
        self._poll_interval = poll_interval
        self._running = False

    async def start(self, bus: EventBus) -> None:
        self._running = True
        while self._running:
            try:
                scores = self._fetch_scores()
                await bus.publish("sentiment.update", SentimentEvent(
                    source=self.name,
                    scores=tuple(scores.items()),
                ))
            except Exception:
                logger.exception("sentiment fetch failed")
            await asyncio.sleep(self._poll_interval)

    async def stop(self) -> None:
        self._running = False

    def run_batch(self, data: dict[str, Any]) -> Any:
        """Batch mode — expects data['hawkishness'] as pd.Series."""
        import pandas as pd
        hawk = data.get("hawkishness")
        if hawk is None:
            return {"scores": {}}
        delta = sentiment_delta(hawk)
        latest = float(delta.iloc[-1]) if not delta.empty and not pd.isna(delta.iloc[-1]) else 0.0
        return {"scores": {"hawkishness": float(hawk.iloc[-1]), "hawk_delta": latest}}

    def _fetch_scores(self) -> dict[str, float]:
        """Live mode — attempts to pull from NewsAPI. Falls back gracefully."""
        import os
        scores: dict[str, float] = {}
        if os.environ.get("NEWSAPI_KEY"):
            try:
                from bigshort.sentiment.news import NewsSource
                from datetime import datetime, timedelta
                end = datetime.utcnow().strftime("%Y-%m-%d")
                start = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
                ns = NewsSource()
                df = ns.fetch_fedspeak(start, end)
                if not df.empty:
                    scores["hawkishness"] = float(df["hawkishness"].iloc[-1])
                    delta = sentiment_delta(df["hawkishness"])
                    if not delta.empty:
                        scores["hawk_delta"] = float(delta.iloc[-1])
            except Exception:
                logger.debug("NewsAPI unavailable")
        return scores
