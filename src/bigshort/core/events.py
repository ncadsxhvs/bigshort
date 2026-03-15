"""Frozen event dataclasses for the EventBus."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Event:
    """Base event — all events inherit from this."""

    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = ""
    error: str | None = None


@dataclass(frozen=True)
class TickEvent(Event):
    ticker: str = ""
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0


@dataclass(frozen=True)
class BatchEvent(Event):
    """Pointer to MarketStore — tickers have been written."""

    tickers: tuple[str, ...] = ()


@dataclass(frozen=True)
class FeatureEvent(Event):
    """Pointer to FeatureStore — features have been written."""

    feature_names: tuple[str, ...] = ()


@dataclass(frozen=True)
class SentimentEvent(Event):
    scores: tuple[tuple[str, float], ...] = ()

    @property
    def scores_dict(self) -> dict[str, float]:
        return dict(self.scores)


@dataclass(frozen=True)
class RegimeEvent(Event):
    old_regime: int = -1
    new_regime: int = -1
    confidence: float = 0.0


@dataclass(frozen=True)
class SignalEvent(Event):
    signals: tuple[tuple[str, int], ...] = ()
    vote: int = 0

    @property
    def signals_dict(self) -> dict[str, int]:
        return dict(self.signals)


@dataclass(frozen=True)
class TradeProposal(Event):
    ticker: str = ""
    side: str = ""  # "buy" | "sell" | "hold"
    size: float = 0.0
    reasoning: str = ""
    confidence: float = 0.0


@dataclass(frozen=True)
class FillEvent(Event):
    ticker: str = ""
    side: str = ""
    price: float = 0.0
    slippage: float = 0.0
