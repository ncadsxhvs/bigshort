# BigShort

Quantamental trading research platform — fuses macroeconomic fundamentals with technical signals to identify edges in Gold and NASDAQ 100 markets.

## Setup

```bash
pip install -e ".[dev]"
```

## Usage

### Pull data and view latest signals

```bash
python -m bigshort
```

This will:
1. Download daily OHLCV data from yfinance for NDX (`^NDX`), Gold (`GC=F`), VIX (`^VIX`), and GVZ (`^GVZ`)
2. Align all assets to the NDX trading calendar (forward-fill missing dates)
3. Cache results as parquet files under `data/`
4. Print the latest 60-day Gold/NDX rolling correlation and VIX/GVZ volatility spread

Subsequent runs load from the parquet cache. Delete files in `data/` to force a fresh pull.

### Load cached data in Python

```python
from bigshort.utils.cache import load_cache

ndx = load_cache("ndx")   # pandas DataFrame with OHLCV columns
gold = load_cache("gold")
vix = load_cache("vix")
gvz = load_cache("gvz")
```

### Compute features

```python
from bigshort.features.correlation import rolling_correlation, volatility_spread

corr = rolling_correlation(gold["close"], ndx["close"], window=60)
vol_spread = volatility_spread(vix["close"], gvz["close"])
```

## Tests

```bash
python -m pytest tests/ -v
```

## Project Structure

```
src/bigshort/
├── config.py              # Tickers, defaults, paths
├── __main__.py            # CLI entry point
├── data/
│   ├── base.py            # Abstract DataSource interface
│   └── yfinance.py        # YFinance connector
├── etl/
│   ├── pipeline.py        # Orchestrates pulls, sync, cache
│   └── sync.py            # Trading calendar alignment
├── features/
│   └── correlation.py     # Rolling correlation, vol spread
└── utils/
    └── cache.py           # Parquet save/load
```
