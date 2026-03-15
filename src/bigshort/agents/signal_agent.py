"""SignalAgent — runs strategies, aggregates via voting."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from bigshort.core.agent import Agent
from bigshort.core.bus import EventBus
from bigshort.core.events import FeatureEvent, RegimeEvent, SignalEvent
from bigshort.core.stores import FeatureStore, MarketStore, SignalStore
from bigshort.strategy.macd_backtest import macd_signals
from bigshort.strategy.rotation import rotation_signals
from bigshort.strategy.straddle import detect_low_vol_entries
from bigshort.strategy.voting import signal_vote
from bigshort.features.macd import macd

logger = logging.getLogger(__name__)


class SignalAgent(Agent):
    name = "signal"

    def __init__(
        self,
        market_store: MarketStore,
        feature_store: FeatureStore,
        signal_store: SignalStore,
    ) -> None:
        self._market = market_store
        self._features = feature_store
        self._signals = signal_store
        self._last_regime: int = 0

    async def start(self, bus: EventBus) -> None:
        feat_q = bus.subscribe("features.ready")
        regime_q = bus.subscribe("regime.change")

        async def watch_regime() -> None:
            while True:
                event: RegimeEvent = await regime_q.get()  # type: ignore[assignment]
                self._last_regime = event.new_regime

        import asyncio
        asyncio.create_task(watch_regime())

        while True:
            event: FeatureEvent = await feat_q.get()  # type: ignore[assignment]
            try:
                result = self._generate()
                if result is not None:
                    self._signals.record_signal(result)
                    await bus.publish("signal.raw", result)
            except Exception:
                logger.exception("signal generation failed")

    def run_batch(self, data: dict[str, Any]) -> Any:
        regime = data.get("regime", 0)
        self._last_regime = regime
        result = self._generate()
        if result is None:
            return {"vote": 0, "signals": {}}
        self._signals.record_signal(result)
        return {"vote": result.vote, "signals": result.signals_dict}

    def _generate(self) -> SignalEvent | None:
        ndx = self._market.get("ndx")
        if ndx.empty:
            return None

        signals: dict[str, pd.Series] = {}

        # MACD signals
        macd_df = macd(ndx["close"])
        signals["macd"] = macd_signals(macd_df)

        # Rotation signals from regime
        regimes = pd.Series(self._last_regime, index=ndx.index, name="regime")
        signals["rotation"] = rotation_signals(regimes)

        # Straddle (low-vol entry as +1)
        vol = self._features.get("ndx_realized_vol")
        if not vol.empty:
            low_vol = detect_low_vol_entries(vol.dropna())
            signals["straddle"] = low_vol.astype(int).reindex(ndx.index, fill_value=0)

        vote_series = signal_vote(signals)

        # Take latest values
        latest_signals = {k: int(v.iloc[-1]) for k, v in signals.items() if not v.empty}
        latest_vote = int(vote_series.iloc[-1]) if not vote_series.empty else 0

        return SignalEvent(
            source=self.name,
            signals=tuple(latest_signals.items()),
            vote=latest_vote,
        )
