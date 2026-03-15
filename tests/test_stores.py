"""Tests for MarketStore, FeatureStore, SignalStore."""

from __future__ import annotations

import pandas as pd
import pytest

from bigshort.core.events import FillEvent, SignalEvent, TradeProposal
from bigshort.core.stores import FeatureStore, MarketStore, SignalStore


@pytest.fixture
def tmp_root(tmp_path):
    return tmp_path


def test_market_store_append_and_get(tmp_root):
    store = MarketStore(root=tmp_root / "market")
    idx = pd.date_range("2024-01-01", periods=3, freq="D")
    df = pd.DataFrame({"close": [100, 101, 102], "volume": [1, 2, 3]}, index=idx)
    store.append("test", df)

    result = store.get("test")
    assert len(result) == 3
    assert result["close"].iloc[-1] == 102


def test_market_store_latest(tmp_root):
    store = MarketStore(root=tmp_root / "market")
    idx = pd.date_range("2024-01-01", periods=2, freq="D")
    df = pd.DataFrame({"close": [10, 20]}, index=idx)
    store.append("x", df)
    assert store.latest("x")["close"] == 20


def test_market_store_empty(tmp_root):
    store = MarketStore(root=tmp_root / "market")
    assert store.get("missing").empty
    assert store.latest("missing").empty


def test_feature_store_put_get(tmp_root):
    store = FeatureStore(root=tmp_root / "features")
    idx = pd.date_range("2024-01-01", periods=5, freq="D")
    s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=idx, name="feat")
    store.put("feat", s)

    result = store.get("feat")
    assert len(result) == 5


def test_feature_store_snapshot(tmp_root):
    store = FeatureStore(root=tmp_root / "features")
    idx = pd.date_range("2024-01-01", periods=3, freq="D")
    store.put("a", pd.Series([1, 2, 3], index=idx))
    store.put("b", pd.Series([4, 5, 6], index=idx))

    snap = store.snapshot()
    assert "a" in snap.columns
    assert "b" in snap.columns
    assert snap["a"].iloc[0] == 3


def test_signal_store_record(tmp_root):
    store = SignalStore(root=tmp_root / "signals")
    sig = SignalEvent(signals=(("macd", 1),), vote=1, source="test")
    store.record_signal(sig)

    prop = TradeProposal(ticker="NDX", side="buy", size=1.0, confidence=0.8, reasoning="test")
    fill = FillEvent(ticker="NDX", side="buy", price=100.05, slippage=0.05)
    store.record_trade(prop, fill)

    portfolio = store.get_portfolio()
    assert portfolio["NDX"] == 1.0

    trades = store.get_trades()
    assert len(trades) == 1
