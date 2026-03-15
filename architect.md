# BigShort Multi-Agent Quant Trading System — Architecture

## Context

Re-architect BigShort from a batch pipeline of pure functions into a **hybrid multi-agent system** that supports both historical research and real-time paper/live trading. Existing feature/strategy code stays as pure-function libraries; agents are thin wrappers that add lifecycle and event-driven coordination. Full rewrite is acceptable.

---

## 1. Agent Taxonomy

| Agent | Type | Mode | Responsibility |
|-------|------|------|----------------|
| **DataAgent** | Software | Continuous (live) / batch (research) | Fetch OHLCV, manage cache, emit tick events |
| **FeatureAgent** | Software | Reactive | Compute all technical features (correlation, Kalman, HA, VIX, MACD, causality) |
| **SentimentAgent** | Software | Periodic (15 min live) / batch | Pull NewsAPI, Reddit; compute sentiment scores |
| **RegimeAgent** | Software | Reactive | Run HMM, detect regime changes |
| **SignalAgent** | Software | Reactive | Run strategies (MACD, straddle, rotation), aggregate via voting |
| **StrategistAgent** | **LLM** | Reactive | Interpret signals, explain anomalies, gate trades, analyze backtests |
| **ExecutionAgent** | Software | Reactive | Simulate or execute trades, track portfolio/PnL |

Only one LLM agent (StrategistAgent) — LLM calls are slow and expensive, so they only fire when there's a real decision to make.

---

## 2. Communication: In-Process EventBus

Single-process `asyncio` pub/sub. No external message broker.

```python
EventBus
  .publish(topic: str, event: Event)
  .subscribe(topic: str) -> asyncio.Queue[Event]
```

### Event Flow

```
DataAgent → market.tick / market.batch
  → FeatureAgent → features.ready
      → RegimeAgent → regime.change
      → SignalAgent → signal.raw
          → StrategistAgent → trade.proposed
              → HumanGate → trade.approved
                  → ExecutionAgent → trade.fill
SentimentAgent → sentiment.update (parallel, feeds into SignalAgent + StrategistAgent)
```

DataFrames are **not** sent through the bus. Agents write to shared stores; events carry timestamps/keys for lookup.

### Event Types (frozen dataclasses)

- `TickEvent(ticker, open, high, low, close, volume)`
- `BatchEvent(tickers: list[str])` — pointer to MarketStore
- `FeatureEvent(feature_names: list[str])` — pointer to FeatureStore
- `SentimentEvent(scores: dict[str, float])`
- `RegimeEvent(old_regime, new_regime, confidence)`
- `SignalEvent(signals: dict[str, int], vote: int)`
- `TradeProposal(ticker, side, size, reasoning, confidence)`
- `FillEvent(ticker, side, price, slippage)`

All inherit from `Event(timestamp, source, error: str | None)`.

---

## 3. Data Architecture — Three Stores

All parquet-backed, no database.

| Store | Key | Persists to |
|-------|-----|-------------|
| **MarketStore** | `(ticker, date)` → OHLCV row | `data/market/{ticker}.parquet` |
| **FeatureStore** | `(feature_name, date)` → float | `data/features/{name}.parquet` |
| **SignalStore** | append-only log | `data/signals/log.parquet` |

```python
class MarketStore:
    get(ticker, start, end) -> DataFrame
    append(ticker, df) -> None
    latest(ticker) -> Series

class FeatureStore:
    put(name, series) -> None
    get(name, start?, end?) -> Series
    snapshot(as_of?) -> DataFrame  # latest row of all features

class SignalStore:
    record_signal(SignalEvent) -> None
    record_trade(TradeProposal, FillEvent) -> None
    get_portfolio() -> Portfolio
    get_pnl() -> Series
```

LLM logs go to `data/llm_logs/` as JSONL.

---

## 4. LLM StrategistAgent Design

### Decisions it makes
1. **Trade gating** — given signal votes + regime + sentiment, decide act/wait
2. **Anomaly explanation** — when regime changes or correlations break
3. **Research analysis** — review backtest results, suggest hypotheses

### Context window (~2000 tokens)
A `ContextBuilder` produces a structured text summary:
- Current regime + confidence
- Signal votes per strategy + consensus
- Latest feature values (small table)
- Sentiment scores
- Current portfolio + last 5 trades

### LLM tools (function calling)
- `lookup_feature(name, lookback_days)`
- `lookup_sentiment(source, lookback_days)`
- `run_backtest(strategy, params, start, end)` — research mode only
- `get_portfolio()`, `get_trade_history(n)`

### Output: structured `TradeDecision`
```
{action: buy|sell|hold, ticker, size, confidence, reasoning}
```

### Human-in-the-loop (`HumanGate`)
- `auto` — proposals go straight to execution (paper trading)
- `approve` — printed to terminal, user types y/n (default for live)
- `observe` — log only, nothing executes

---

## 5. Agent Protocol

```python
class Agent(Protocol):
    name: str
    async def start(self, bus: EventBus) -> None: ...   # subscribe + run loop
    async def stop(self) -> None: ...                     # graceful shutdown
    def run_batch(self, data: dict) -> Any: ...           # synchronous research mode
```

Features, strategies, and sentiment remain **pure functions with zero agent awareness**. Agents are thin wrappers. Existing tests stay valid.

---

## 6. Package Structure

```
src/bigshort/
    __init__.py
    __main__.py              # CLI: research | paper | live
    config.py                # extended with agent/LLM/gate settings

    core/                    # NEW — infrastructure
        __init__.py
        events.py            # Event dataclasses
        bus.py               # EventBus (asyncio pub/sub)
        agent.py             # Agent protocol/ABC
        orchestrator.py      # research + live runners
        stores.py            # MarketStore, FeatureStore, SignalStore

    agents/                  # NEW — agent wrappers
        __init__.py
        data_agent.py
        feature_agent.py
        sentiment_agent.py
        regime_agent.py
        signal_agent.py
        strategist.py        # LLM agent
        execution_agent.py
        context.py           # ContextBuilder for LLM prompts
        human_gate.py

    data/                    # KEPT — pure connectors
        __init__.py
        base.py
        yfinance.py
        fred.py

    features/                # KEPT — pure functions
        __init__.py
        correlation.py, kalman.py, heikin_ashi.py,
        vix_calc.py, macd.py, causality.py

    sentiment/               # KEPT — connectors + features
        __init__.py
        news.py, reddit.py, features.py

    strategy/                # KEPT — pure signal/backtest functions
        __init__.py
        hmm.py, rotation.py, straddle.py, macd_backtest.py,
        voting.py, execution.py

    reporting/               # MOVED from strategy/report.py
        __init__.py
        report.py
        dashboard.py         # optional terminal dashboard

    utils/
        __init__.py
        cache.py
```

---

## 7. Execution Modes

### Research (synchronous, no asyncio)
```bash
python3 -m bigshort research --start 2020-01-01 --end 2024-12-31
```
Calls `agent.run_batch()` in pipeline order. Same as current codebase but formalized.

### Paper Trading (async event loop)
```bash
python3 -m bigshort paper --poll-interval 60
```
DataAgent polls every 60s. All agents run as asyncio tasks. HumanGate = auto. ExecutionAgent simulates fills with slippage.

### Live (future)
```bash
python3 -m bigshort live --broker alpaca
```
Same as paper but ExecutionAgent connects to real broker. HumanGate = approve.

---

## 8. Key Design Decisions

- **One LLM agent, not many** — simpler, cheaper, single prompt templates
- **EventBus is in-process only** — swap for Redis Streams later if needed; Agent protocol unchanged
- **Stores over databases** — parquet is fast, human-readable, zero setup
- **Research mode skips asyncio** — batch doesn't benefit from async; debugging is trivial
- **Pure functions stay pure** — agents wrap, never replace; all existing tests keep working
