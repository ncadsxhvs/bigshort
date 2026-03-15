"""DataAgent — fetches OHLCV, writes to MarketStore, emits events."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from bigshort.core.agent import Agent
from bigshort.core.bus import EventBus
from bigshort.core.events import BatchEvent, TickEvent
from bigshort.core.stores import MarketStore
from bigshort.data.yfinance import YFinanceSource
from bigshort.etl.sync import align_to_trading_calendar
from bigshort import config

logger = logging.getLogger(__name__)


class DataAgent(Agent):
    name = "data"

    def __init__(
        self,
        market_store: MarketStore,
        tickers: dict[str, str] | None = None,
        source: YFinanceSource | None = None,
        poll_interval: float = 60.0,
    ) -> None:
        self._store = market_store
        self._source = source or YFinanceSource()
        self._poll_interval = poll_interval
        self._running = False
        self._assets = tickers or dict(config.DEFAULT_TICKERS)

    async def start(self, bus: EventBus) -> None:
        self._running = True
        while self._running:
            try:
                tickers = self._fetch_and_store()
                await bus.publish("market.batch", BatchEvent(
                    source=self.name,
                    tickers=tuple(tickers),
                ))
            except Exception:
                logger.exception("data fetch failed")
            await asyncio.sleep(self._poll_interval)

    async def stop(self) -> None:
        self._running = False

    def run_batch(self, data: dict[str, Any]) -> Any:
        start = data.get("start", config.DEFAULT_START)
        end = data.get("end", config.DEFAULT_END)
        frames = {}
        for key, ticker in self._assets.items():
            frames[key] = self._source.fetch(ticker, start=start, end=end)
        aligned = align_to_trading_calendar(frames, reference_key="ndx")
        for key, df in aligned.items():
            self._store.append(key, df)
        return {"tickers": list(aligned.keys())}

    def _fetch_and_store(self) -> list[str]:
        frames = {}
        for key, ticker in self._assets.items():
            frames[key] = self._source.fetch(ticker, start=config.DEFAULT_START)
        aligned = align_to_trading_calendar(frames, reference_key="ndx")
        for key, df in aligned.items():
            self._store.append(key, df)
        return list(aligned.keys())
