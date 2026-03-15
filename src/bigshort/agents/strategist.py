"""StrategistAgent — the single LLM agent for trade gating and analysis."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from bigshort.core.agent import Agent
from bigshort.core.bus import EventBus
from bigshort.core.events import (
    RegimeEvent,
    SentimentEvent,
    SignalEvent,
    TradeProposal,
)
from bigshort.core.stores import FeatureStore, SignalStore
from bigshort.agents.context import ContextBuilder
from bigshort.agents.human_gate import HumanGate
from bigshort.config import CACHE_DIR

logger = logging.getLogger(__name__)

LLM_LOG_DIR = CACHE_DIR / "llm_logs"


class StrategistAgent(Agent):
    name = "strategist"

    def __init__(
        self,
        feature_store: FeatureStore,
        signal_store: SignalStore,
        gate: HumanGate | None = None,
        llm_client: Any = None,
    ) -> None:
        self._ctx = ContextBuilder(feature_store, signal_store)
        self._gate = gate or HumanGate(mode="observe")
        self._llm = llm_client
        self._last_regime: RegimeEvent | None = None
        self._last_sentiment: SentimentEvent | None = None

    async def start(self, bus: EventBus) -> None:
        signal_q = bus.subscribe("signal.raw")
        regime_q = bus.subscribe("regime.change")
        sentiment_q = bus.subscribe("sentiment.update")

        import asyncio

        async def watch_regime() -> None:
            while True:
                self._last_regime = await regime_q.get()  # type: ignore[assignment]

        async def watch_sentiment() -> None:
            while True:
                self._last_sentiment = await sentiment_q.get()  # type: ignore[assignment]

        asyncio.create_task(watch_regime())
        asyncio.create_task(watch_sentiment())

        while True:
            signal: SignalEvent = await signal_q.get()  # type: ignore[assignment]
            try:
                proposal = self._decide(signal)
                if proposal and proposal.side != "hold":
                    if self._gate.check(proposal):
                        await bus.publish("trade.approved", proposal)
                    else:
                        await bus.publish("trade.proposed", proposal)
            except Exception:
                logger.exception("strategist decision failed")

    def run_batch(self, data: dict[str, Any]) -> Any:
        vote = data.get("vote", 0)
        signals = data.get("signals", {})
        signal_event = SignalEvent(
            source="batch",
            signals=tuple(signals.items()),
            vote=vote,
        )
        proposal = self._decide(signal_event)
        return {
            "proposal": proposal,
            "side": proposal.side if proposal else "hold",
        }

    def _decide(self, signal: SignalEvent) -> TradeProposal | None:
        context = self._ctx.build(
            regime=self._last_regime,
            signal=signal,
            sentiment=self._last_sentiment,
        )

        # If LLM client available, use it
        if self._llm is not None:
            return self._llm_decide(context, signal)

        # Fallback: rule-based decision from vote
        return self._rule_decide(signal)

    def _rule_decide(self, signal: SignalEvent) -> TradeProposal:
        """Simple rule-based fallback when no LLM is configured."""
        if signal.vote > 0:
            return TradeProposal(
                source=self.name,
                ticker="NDX",
                side="buy",
                size=1.0,
                confidence=0.5,
                reasoning=f"signal vote={signal.vote}, rule-based",
            )
        elif signal.vote < 0:
            return TradeProposal(
                source=self.name,
                ticker="NDX",
                side="sell",
                size=1.0,
                confidence=0.5,
                reasoning=f"signal vote={signal.vote}, rule-based",
            )
        return TradeProposal(
            source=self.name,
            ticker="NDX",
            side="hold",
            size=0.0,
            confidence=1.0,
            reasoning="no consensus",
        )

    def _llm_decide(self, context: str, signal: SignalEvent) -> TradeProposal:
        """Call the LLM for a trade decision."""
        prompt = (
            "You are a quantitative trading strategist. Given the market context below, "
            "decide whether to buy, sell, or hold. Respond with JSON: "
            '{"action": "buy"|"sell"|"hold", "ticker": "...", "size": float, '
            '"confidence": float, "reasoning": "..."}\n\n'
            f"{context}"
        )

        try:
            response = self._llm.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text
            self._log_llm(prompt, text)
            decision = json.loads(text)
            return TradeProposal(
                source=self.name,
                ticker=decision.get("ticker", "NDX"),
                side=decision.get("action", "hold"),
                size=float(decision.get("size", 0)),
                confidence=float(decision.get("confidence", 0)),
                reasoning=decision.get("reasoning", ""),
            )
        except Exception:
            logger.exception("LLM call failed, falling back to rules")
            return self._rule_decide(signal)

    def _log_llm(self, prompt: str, response: str) -> None:
        LLM_LOG_DIR.mkdir(parents=True, exist_ok=True)
        path = LLM_LOG_DIR / "decisions.jsonl"
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "prompt": prompt,
            "response": response,
        }
        with open(path, "a") as f:
            f.write(json.dumps(entry) + "\n")
