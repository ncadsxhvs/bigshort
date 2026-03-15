"""HumanGate — controls whether trade proposals proceed to execution."""

from __future__ import annotations

import logging

from bigshort.core.events import TradeProposal

logger = logging.getLogger(__name__)


class HumanGate:
    """Trade approval gate.

    Modes:
        auto    — proposals go straight to execution (paper trading)
        approve — printed to terminal, user types y/n (live trading)
        observe — log only, nothing executes
    """

    def __init__(self, mode: str = "auto") -> None:
        if mode not in ("auto", "approve", "observe"):
            raise ValueError(f"invalid gate mode: {mode!r}")
        self.mode = mode

    def check(self, proposal: TradeProposal) -> bool:
        """Return True if the proposal should proceed to execution."""
        summary = (
            f"[{proposal.side.upper()}] {proposal.ticker} "
            f"size={proposal.size:.2f} confidence={proposal.confidence:.2f}\n"
            f"  reason: {proposal.reasoning}"
        )

        if self.mode == "observe":
            logger.info("observe: %s", summary)
            return False

        if self.mode == "auto":
            logger.info("auto-approved: %s", summary)
            return True

        # approve mode
        print(f"\n{'='*60}")
        print(f"TRADE PROPOSAL: {summary}")
        print(f"{'='*60}")
        response = input("Approve? [y/N] ").strip().lower()
        approved = response == "y"
        if not approved:
            logger.info("rejected by user: %s", summary)
        return approved
