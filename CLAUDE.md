# BigShort Development Guide

## Environment
- Python 3.9.6 (system Xcode python at /usr/bin/python3)
- Use `python3 -m pip` and `python3 -m pytest` (no bare `pip`/`pytest` on PATH)
- `requires-python = ">=3.9"` — use `from __future__ import annotations` for modern type syntax
- pyproject.toml uses `setuptools.build_meta` backend (not `setuptools.backends._legacy`)

## Project Structure
- src layout: `src/bigshort/` with editable install via `pip install -e ".[dev]"`
- Parquet cache in `data/` (gitignored)

```
src/bigshort/
    __init__.py
    __main__.py              # CLI: research | paper | live
    config.py                # agent/LLM/gate settings

    core/                    # Infrastructure
        events.py            # Event dataclasses (frozen)
        bus.py               # EventBus (asyncio pub/sub)
        agent.py             # Agent protocol/ABC
        orchestrator.py      # research + live runners
        stores.py            # MarketStore, FeatureStore, SignalStore

    agents/                  # Thin agent wrappers
        data_agent.py
        feature_agent.py
        sentiment_agent.py
        regime_agent.py
        signal_agent.py
        strategist.py        # LLM agent (only LLM agent)
        execution_agent.py
        context.py           # ContextBuilder for LLM prompts
        human_gate.py

    data/                    # Pure connectors (unchanged)
    features/                # Pure functions (unchanged)
    sentiment/               # Connectors + features (unchanged)
    strategy/                # Pure signal/backtest functions (unchanged)
    reporting/               # Reports + optional dashboard
    utils/
```

## Architecture
- **Hybrid multi-agent**: pure-function libraries wrapped by thin agents
- **EventBus**: in-process `asyncio` pub/sub (no external broker)
- **Three stores**: MarketStore, FeatureStore, SignalStore — all parquet-backed
- **One LLM agent**: StrategistAgent only — gates trades, explains anomalies
- **Three modes**: `research` (sync batch), `paper` (async polling), `live` (future)
- DataFrames are NOT sent through the bus — agents write to shared stores, events carry keys
- Pure functions stay pure — agents wrap, never replace; existing tests stay valid

## Agent Protocol
```python
class Agent(Protocol):
    name: str
    async def start(self, bus: EventBus) -> None
    async def stop(self) -> None
    def run_batch(self, data: dict) -> Any
```

## Event Flow
```
DataAgent → market.tick/batch → FeatureAgent → features.ready
  → RegimeAgent → regime.change
  → SignalAgent → signal.raw → StrategistAgent → trade.proposed
    → HumanGate → trade.approved → ExecutionAgent → trade.fill
SentimentAgent → sentiment.update (parallel)
```

## Testing
- `python3 -m pytest tests/ -v` — all connectors use mocked API responses
- Mock yfinance with `patch("bigshort.data.yfinance.yf.download")`
- Mock FRED with `patch("bigshort.data.fred.Fred")`
- Mock EventBus for agent tests

## Event Types (frozen dataclasses, inherit from Event)
- `Event(timestamp, source, error: str | None)` — base
- `TickEvent(ticker, open, high, low, close, volume)`
- `BatchEvent(tickers: list[str])` — pointer to MarketStore
- `FeatureEvent(feature_names: list[str])` — pointer to FeatureStore
- `SentimentEvent(scores: dict[str, float])`
- `RegimeEvent(old_regime, new_regime, confidence)`
- `SignalEvent(signals: dict[str, int], vote: int)`
- `TradeProposal(ticker, side, size, reasoning, confidence)`
- `FillEvent(ticker, side, price, slippage)`

## Store APIs
```python
class MarketStore:
    get(ticker, start, end) -> DataFrame
    append(ticker, df) -> None
    latest(ticker) -> Series

class FeatureStore:
    put(name, series) -> None
    get(name, start?, end?) -> Series
    snapshot(as_of?) -> DataFrame

class SignalStore:
    record_signal(SignalEvent) -> None
    record_trade(TradeProposal, FillEvent) -> None
    get_portfolio() -> Portfolio
    get_pnl() -> Series
```

## Execution Modes
- `python3 -m bigshort research --start 2020-01-01 --end 2024-12-31` — sync batch, no asyncio
- `python3 -m bigshort paper --poll-interval 60` — async event loop, HumanGate=auto
- `python3 -m bigshort live --broker alpaca` — async, HumanGate=approve

## StrategistAgent LLM Tools (function calling)
- `lookup_feature(name, lookback_days)`
- `lookup_sentiment(source, lookback_days)`
- `run_backtest(strategy, params, start, end)` — research mode only
- `get_portfolio()`, `get_trade_history(n)`

## Tech Stack
- asyncio (in-process pub/sub), Pandas, Parquet, NumPy, SciPy
- scikit-learn, statsmodels, hmmlearn (ML)
- Anthropic Claude API (LLM)

## Config
- FRED API key via `FRED_API_KEY` env var
- HumanGate modes: `auto` (paper), `approve` (live), `observe` (log only)
- Run with `python3 -m bigshort research|paper|live`
