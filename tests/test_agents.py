"""Tests for agent batch mode (no asyncio needed)."""

from __future__ import annotations

import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from bigshort.core.stores import MarketStore, FeatureStore, SignalStore
from bigshort.agents.data_agent import DataAgent
from bigshort.agents.feature_agent import FeatureAgent
from bigshort.agents.regime_agent import RegimeAgent
from bigshort.agents.signal_agent import SignalAgent
from bigshort.agents.strategist import StrategistAgent
from bigshort.agents.execution_agent import ExecutionAgent
from bigshort.agents.human_gate import HumanGate
from bigshort.agents.context import ContextBuilder
from bigshort.core.events import RegimeEvent, SignalEvent, TradeProposal


@pytest.fixture
def stores(tmp_path):
    return (
        MarketStore(root=tmp_path / "market"),
        FeatureStore(root=tmp_path / "features"),
        SignalStore(root=tmp_path / "signals"),
    )


def _seed_market(market: MarketStore) -> None:
    """Put synthetic OHLCV data into the market store."""
    idx = pd.date_range("2023-01-01", periods=200, freq="B")
    import numpy as np
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(200) * 0.5)
    df = pd.DataFrame({
        "open": close - 0.5,
        "high": close + 1,
        "low": close - 1,
        "close": close,
        "volume": np.random.randint(1000, 10000, 200),
    }, index=idx)
    for key in ("ndx", "gold", "vix", "gvz"):
        market.append(key, df)


def test_data_agent_batch(stores):
    market, features, signals = stores
    agent = DataAgent(market)
    mock_df = pd.DataFrame(
        {"open": [1], "high": [2], "low": [0.5], "close": [1.5], "volume": [100]},
        index=pd.DatetimeIndex(["2024-01-02"]),
    )
    mock_df.index.name = "date"
    with patch("bigshort.agents.data_agent.YFinanceSource") as MockYF:
        src = MockYF.return_value
        src.fetch.return_value = mock_df
        agent._source = src
        result = agent.run_batch({"start": "2024-01-01", "end": "2024-01-31"})
    assert "tickers" in result


def test_feature_agent_batch(stores):
    market, features, signals = stores
    _seed_market(market)
    agent = FeatureAgent(market, features)
    result = agent.run_batch({})
    assert "feature_names" in result
    assert len(result["feature_names"]) > 0
    assert "gold_ndx_corr" in result["feature_names"]


def test_regime_agent_batch(stores):
    market, features, signals = stores
    _seed_market(market)
    # First compute features
    feat_agent = FeatureAgent(market, features)
    feat_agent.run_batch({})
    # Then detect regime
    agent = RegimeAgent(features)
    result = agent.run_batch({})
    assert "regime" in result
    assert result["regime"] in (0, 1)


def test_signal_agent_batch(stores):
    market, features, signals = stores
    _seed_market(market)
    feat_agent = FeatureAgent(market, features)
    feat_agent.run_batch({})
    agent = SignalAgent(market, features, signals)
    result = agent.run_batch({"regime": 0})
    assert "vote" in result
    assert "signals" in result


def test_strategist_rule_based(stores):
    market, features, signals = stores
    agent = StrategistAgent(features, signals, gate=HumanGate(mode="observe"))
    result = agent.run_batch({"vote": 1, "signals": {"macd": 1}})
    assert result["side"] == "buy"

    result = agent.run_batch({"vote": -1, "signals": {"macd": -1}})
    assert result["side"] == "sell"

    result = agent.run_batch({"vote": 0, "signals": {}})
    assert result["side"] == "hold"


def test_execution_agent_batch(stores):
    market, features, signals = stores
    _seed_market(market)
    from bigshort.core.events import TradeProposal
    proposal = TradeProposal(ticker="NDX", side="buy", size=1.0, confidence=0.8, reasoning="test")
    agent = ExecutionAgent(market, signals)
    result = agent.run_batch({"proposal": proposal})
    assert result["filled"] is True
    assert result["price"] > 0


def test_human_gate_auto():
    gate = HumanGate(mode="auto")
    p = TradeProposal(ticker="X", side="buy", size=1, confidence=0.5, reasoning="t")
    assert gate.check(p) is True


def test_human_gate_observe():
    gate = HumanGate(mode="observe")
    p = TradeProposal(ticker="X", side="buy", size=1, confidence=0.5, reasoning="t")
    assert gate.check(p) is False


def test_human_gate_invalid():
    with pytest.raises(ValueError):
        HumanGate(mode="invalid")


def test_context_builder(stores):
    market, features, signals = stores
    _seed_market(market)
    feat_agent = FeatureAgent(market, features)
    feat_agent.run_batch({})

    builder = ContextBuilder(features, signals)
    regime = RegimeEvent(old_regime=0, new_regime=1, confidence=0.9)
    signal = SignalEvent(signals=(("macd", 1),), vote=1)
    context = builder.build(regime=regime, signal=signal)
    assert "Safe-Haven" in context
    assert "macd" in context
