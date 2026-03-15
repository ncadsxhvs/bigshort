"""Tests for core event dataclasses."""

from __future__ import annotations

from bigshort.core.events import (
    BatchEvent,
    Event,
    FeatureEvent,
    FillEvent,
    RegimeEvent,
    SentimentEvent,
    SignalEvent,
    TickEvent,
    TradeProposal,
)


def test_event_is_frozen():
    e = Event(source="test")
    try:
        e.source = "other"  # type: ignore[misc]
        assert False, "should be frozen"
    except AttributeError:
        pass


def test_tick_event_fields():
    t = TickEvent(ticker="AAPL", close=150.0, volume=1_000_000)
    assert t.ticker == "AAPL"
    assert t.close == 150.0


def test_batch_event_tickers():
    b = BatchEvent(tickers=("ndx", "gold"))
    assert "ndx" in b.tickers


def test_signal_event_dict():
    s = SignalEvent(signals=(("macd", 1), ("rotation", -1)), vote=0)
    assert s.signals_dict == {"macd": 1, "rotation": -1}


def test_sentiment_event_dict():
    s = SentimentEvent(scores=(("hawkishness", 0.5),))
    assert s.scores_dict == {"hawkishness": 0.5}


def test_regime_event():
    r = RegimeEvent(old_regime=0, new_regime=1, confidence=0.95)
    assert r.new_regime == 1


def test_trade_proposal():
    p = TradeProposal(ticker="NDX", side="buy", size=1.0, confidence=0.8, reasoning="test")
    assert p.side == "buy"


def test_fill_event():
    f = FillEvent(ticker="NDX", side="buy", price=100.05, slippage=0.05)
    assert f.slippage == 0.05
