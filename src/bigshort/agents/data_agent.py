"""DataAgent — fetches OHLCV + FRED data, writes to MarketStore, emits events."""

from __future__ import annotations

import asyncio
import logging
import os
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

        # YFinance data
        frames = {}
        for key, ticker in self._assets.items():
            frames[key] = self._source.fetch(ticker, start=start, end=end)
        aligned = align_to_trading_calendar(frames, reference_key="ndx")
        for key, df in aligned.items():
            self._store.append(key, df)

        # FRED data
        fred_keys = self._fetch_fred(start, end)

        all_keys = list(aligned.keys()) + fred_keys
        return {"tickers": all_keys}

    def _fetch_and_store(self) -> list[str]:
        frames = {}
        for key, ticker in self._assets.items():
            frames[key] = self._source.fetch(ticker, start=config.DEFAULT_START)
        aligned = align_to_trading_calendar(frames, reference_key="ndx")
        for key, df in aligned.items():
            self._store.append(key, df)

        fred_keys = self._fetch_fred(config.DEFAULT_START)
        return list(aligned.keys()) + fred_keys

    def _fetch_fred(self, start: str, end: str | None = None) -> list[str]:
        """Fetch FRED series if API key is available."""
        from bigshort import config as _  # noqa: ensure dotenv loaded
        if not os.environ.get("FRED_API_KEY"):
            logger.debug("FRED_API_KEY not set, skipping FRED data")
            return []
        try:
            from bigshort.data.fred import FredSource
            fred = FredSource()
            frames = fred.fetch_all(start=start, end=end)
            for key, df in frames.items():
                self._store.append(key, df)
            logger.info("FRED: loaded %s", ", ".join(frames.keys()))
            return list(frames.keys())
        except Exception:
            logger.exception("FRED fetch failed")
            return []
