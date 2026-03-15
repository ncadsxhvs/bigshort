"""FeatureAgent — computes technical features, writes to FeatureStore."""

from __future__ import annotations

import logging
from typing import Any

from bigshort.core.agent import Agent
from bigshort.core.bus import EventBus
from bigshort.core.events import BatchEvent, FeatureEvent
from bigshort.core.stores import FeatureStore, MarketStore
from bigshort.features.correlation import rolling_correlation, volatility_spread
from bigshort.features.kalman import kalman_smooth
from bigshort.features.heikin_ashi import heikin_ashi
from bigshort.features.vix_calc import realized_vol_index
from bigshort.features.macd import macd

logger = logging.getLogger(__name__)


class FeatureAgent(Agent):
    name = "features"

    def __init__(self, market_store: MarketStore, feature_store: FeatureStore) -> None:
        self._market = market_store
        self._features = feature_store

    async def start(self, bus: EventBus) -> None:
        q = bus.subscribe("market.batch")
        while True:
            event: BatchEvent = await q.get()  # type: ignore[assignment]
            try:
                names = self._compute_all()
                await bus.publish("features.ready", FeatureEvent(
                    source=self.name,
                    feature_names=tuple(names),
                ))
            except Exception:
                logger.exception("feature computation failed")

    def run_batch(self, data: dict[str, Any]) -> Any:
        names = self._compute_all()
        return {"feature_names": names}

    def _compute_all(self) -> list[str]:
        names: list[str] = []

        gold = self._market.get("gold")
        ndx = self._market.get("ndx")
        vix = self._market.get("vix")
        gvz = self._market.get("gvz")

        if not gold.empty and not ndx.empty:
            corr = rolling_correlation(gold["close"], ndx["close"])
            self._features.put("gold_ndx_corr", corr)
            names.append("gold_ndx_corr")

        if not vix.empty and not gvz.empty:
            vs = volatility_spread(vix["close"], gvz["close"])
            self._features.put("vol_spread", vs)
            names.append("vol_spread")

        if not gold.empty:
            self._features.put("gold_kalman", kalman_smooth(gold["close"]))
            names.append("gold_kalman")

        if not ndx.empty:
            self._features.put("ndx_kalman", kalman_smooth(ndx["close"]))
            names.append("ndx_kalman")

            vol = realized_vol_index(ndx["close"])
            self._features.put("ndx_realized_vol", vol)
            names.append("ndx_realized_vol")

            macd_df = macd(ndx["close"])
            self._features.put("ndx_macd_line", macd_df["macd_line"])
            self._features.put("ndx_macd_signal", macd_df["signal_line"])
            self._features.put("ndx_macd_hist", macd_df["histogram"])
            names.extend(["ndx_macd_line", "ndx_macd_signal", "ndx_macd_hist"])

        if not ndx.empty and {"open", "high", "low", "close"} <= set(ndx.columns):
            ha = heikin_ashi(ndx)
            self._features.put("ndx_ha_close", ha["ha_close"])
            names.append("ndx_ha_close")

        return names
