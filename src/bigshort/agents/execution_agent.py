"""ExecutionAgent — simulates or executes trades, tracks PnL."""

from __future__ import annotations

import logging
from typing import Any

from bigshort.core.agent import Agent
from bigshort.core.bus import EventBus
from bigshort.core.events import FillEvent, TradeProposal
from bigshort.core.stores import MarketStore, SignalStore
from bigshort.strategy.execution import apply_slippage

logger = logging.getLogger(__name__)


class ExecutionAgent(Agent):
    name = "execution"

    def __init__(self, market_store: MarketStore, signal_store: SignalStore) -> None:
        self._market = market_store
        self._signals = signal_store

    async def start(self, bus: EventBus) -> None:
        q = bus.subscribe("trade.approved")
        while True:
            proposal: TradeProposal = await q.get()  # type: ignore[assignment]
            try:
                fill = self._execute(proposal)
                self._signals.record_trade(proposal, fill)
                await bus.publish("trade.fill", fill)
            except Exception:
                logger.exception("execution failed")

    def run_batch(self, data: dict[str, Any]) -> Any:
        proposal = data.get("proposal")
        if proposal is None or proposal.side == "hold":
            return {"filled": False}
        fill = self._execute(proposal)
        self._signals.record_trade(proposal, fill)
        return {"filled": True, "price": fill.price, "slippage": fill.slippage}

    def _execute(self, proposal: TradeProposal) -> FillEvent:
        """Simulate fill with slippage."""
        latest = self._market.latest(proposal.ticker.lower())
        if latest.empty:
            # Use ticker mappings: NDX->ndx, GOLD->gold
            for key in ("ndx", "gold"):
                latest = self._market.latest(key)
                if not latest.empty:
                    break

        base_price = float(latest.get("close", 100.0)) if not latest.empty else 100.0
        fill_price = apply_slippage(base_price, proposal.side)
        slippage = abs(fill_price - base_price)

        logger.info(
            "filled: %s %s @ %.2f (slip=%.4f)",
            proposal.side, proposal.ticker, fill_price, slippage,
        )

        return FillEvent(
            source=self.name,
            ticker=proposal.ticker,
            side=proposal.side,
            price=fill_price,
            slippage=slippage,
        )
