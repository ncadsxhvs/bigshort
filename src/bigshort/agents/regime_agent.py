"""RegimeAgent — runs HMM, detects regime changes."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from bigshort.core.agent import Agent
from bigshort.core.bus import EventBus
from bigshort.core.events import FeatureEvent, RegimeEvent
from bigshort.core.stores import FeatureStore
from bigshort.strategy.hmm import fit_regime_hmm, predict_regimes

logger = logging.getLogger(__name__)


class RegimeAgent(Agent):
    name = "regime"

    def __init__(self, feature_store: FeatureStore) -> None:
        self._features = feature_store
        self._last_regime: int = -1

    async def start(self, bus: EventBus) -> None:
        q = bus.subscribe("features.ready")
        while True:
            event: FeatureEvent = await q.get()  # type: ignore[assignment]
            try:
                result = self._detect()
                if result is not None:
                    await bus.publish("regime.change", result)
            except Exception:
                logger.exception("regime detection failed")

    def run_batch(self, data: dict[str, Any]) -> Any:
        result = self._detect()
        if result is None:
            return {"regime": -1, "confidence": 0.0}
        return {"regime": result.new_regime, "confidence": result.confidence}

    def _detect(self) -> RegimeEvent | None:
        corr = self._features.get("gold_ndx_corr").dropna()
        vs = self._features.get("vol_spread").dropna()
        if corr.empty or vs.empty:
            return None

        features_df = pd.concat([corr, vs], axis=1).dropna()
        if len(features_df) < 30:
            return None

        model = fit_regime_hmm(features_df)
        regimes = predict_regimes(model, features_df)
        current = int(regimes.iloc[-1])

        posteriors = model.predict_proba(features_df.values)
        confidence = float(posteriors[-1, current])

        old = self._last_regime
        self._last_regime = current
        return RegimeEvent(
            source=self.name,
            old_regime=old,
            new_regime=current,
            confidence=confidence,
        )
