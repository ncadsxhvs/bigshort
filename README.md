# BigShort

Quantamental trading research platform — fuses macroeconomic fundamentals with technical signals to identify edges in Gold and NASDAQ 100 markets.

## Setup

```bash
python3 -m pip install -e ".[dev]"
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FRED_API_KEY` | Optional | FRED economic data access |
| `NEWSAPI_KEY` | Optional | NewsAPI Fedspeak sentiment |

## Quick Start

```bash
# Pull data and view latest signals
python3 -m bigshort

# Run tests
python3 -m pytest tests/ -v
```

`python3 -m bigshort` downloads daily OHLCV for NDX, Gold, VIX, and GVZ from Yahoo Finance, aligns to the NDX trading calendar, caches as parquet under `data/`, and prints the latest correlation and vol spread. Delete files in `data/` to force a fresh pull.

## Usage

### Load cached data

```python
from bigshort.utils.cache import load_cache

ndx = load_cache("ndx")   # pandas DataFrame with OHLCV columns
gold = load_cache("gold")
```

### Features

```python
from bigshort.features.correlation import rolling_correlation, volatility_spread
from bigshort.features.kalman import kalman_smooth
from bigshort.features.heikin_ashi import heikin_ashi
from bigshort.features.vix_calc import realized_vol_index

corr = rolling_correlation(gold["close"], ndx["close"], window=60)
vol_spread = volatility_spread(vix["close"], gvz["close"])
smoothed = kalman_smooth(gold["close"])
ha = heikin_ashi(ndx[["open", "high", "low", "close"]])
vol = realized_vol_index(ndx["close"], window=21)
```

### Sentiment

```python
from bigshort.sentiment.news import NewsSource
from bigshort.sentiment.reddit import RedditSource
from bigshort.sentiment.features import sentiment_delta
from bigshort.features.causality import granger_test

news = NewsSource()  # requires NEWSAPI_KEY
df = news.fetch_fedspeak(start="2024-01-01", end="2024-03-01")
delta = sentiment_delta(df["hawkishness"])
result = granger_test(df["hawkishness"], ndx_returns, max_lag=5)
```

### Strategy

```python
from bigshort.strategy.hmm import fit_regime_hmm, predict_regimes
from bigshort.strategy.rotation import run_rotation_backtest
from bigshort.strategy.straddle import detect_low_vol_entries, straddle_pnl
from bigshort.strategy.execution import simulate_execution
from bigshort.strategy.voting import signal_vote
from bigshort.strategy.report import backtest_report

# HMM regime detection
model = fit_regime_hmm(features[["returns", "volatility"]], n_regimes=2)
regimes = predict_regimes(model, features[["returns", "volatility"]])

# NDX/Gold rotation backtest
result = run_rotation_backtest(ndx_prices, gold_prices, regimes)
print(result["report"])  # sharpe_ratio, max_drawdown, total_return, ...

# Signal voting
combined = signal_vote({"technical": sig1, "macro": sig2}, threshold=0.6)
```

## Project Structure

```
src/bigshort/
├── config.py                # Tickers, defaults, paths
├── __main__.py              # CLI entry point
├── data/
│   ├── base.py              # Abstract DataSource interface
│   └── yfinance.py          # YFinance connector
├── etl/
│   ├── pipeline.py          # Orchestrates pulls, sync, cache
│   └── sync.py              # Trading calendar alignment
├── features/
│   ├── correlation.py       # Rolling correlation, vol spread
│   ├── kalman.py            # 1D Kalman filter denoiser
│   ├── heikin_ashi.py       # Heikin-Ashi OHLC smoothing
│   ├── vix_calc.py          # Realized volatility index
│   └── causality.py         # Granger causality testing
├── sentiment/
│   ├── news.py              # NewsAPI Fedspeak connector
│   ├── reddit.py            # Reddit r/WSB ticker mentions
│   └── features.py          # Sentiment delta scoring
├── strategy/
│   ├── hmm.py               # HMM regime detector
│   ├── rotation.py          # NDX↔Gold rotation backtest
│   ├── straddle.py          # Options straddle entry logic
│   ├── execution.py         # VWAP sim + slippage
│   ├── voting.py            # Signal voting system
│   └── report.py            # Backtest metrics (Sharpe, drawdown)
└── utils/
    └── cache.py             # Parquet save/load + CSV export
```

## Core Assets

| Ticker | Asset | Role |
|--------|-------|------|
| `^NDX` | NASDAQ 100 | Risk-on equity proxy |
| `GC=F` | Gold Futures | Safe-haven proxy |
| `^VIX` | CBOE VIX | Equity implied vol |
| `^GVZ` | CBOE Gold VIX | Gold implied vol |
