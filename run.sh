#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-research}"

# Build --tickers flag if TICKERS env var is set
TICKER_FLAG=""
if [ -n "${TICKERS:-}" ]; then
  TICKER_FLAG="--tickers ${TICKERS}"
fi

case "$MODE" in
  research)
    echo "Running research backtest..."
    python3 -m bigshort research \
      --start "${START:-2018-01-01}" \
      --end "${END:-}" \
      $TICKER_FLAG
    ;;
  paper)
    echo "Starting paper trading..."
    python3 -m bigshort paper \
      --poll-interval "${POLL_INTERVAL:-60}" \
      $TICKER_FLAG
    ;;
  live)
    echo "Starting live trading..."
    python3 -m bigshort live \
      --poll-interval "${POLL_INTERVAL:-60}" \
      --broker "${BROKER:-alpaca}" \
      $TICKER_FLAG
    ;;
  test)
    echo "Running tests..."
    python3 -m pytest tests/ -v
    ;;
  setup)
    echo "Installing bigshort..."
    python3 -m pip install -e ".[dev]"
    ;;
  *)
    echo "Usage: ./run.sh [research|paper|live|test|setup]"
    echo ""
    echo "  research  Run batch backtest (default)"
    echo "  paper     Paper trading with simulated execution"
    echo "  live      Live trading with human approval"
    echo "  test      Run test suite"
    echo "  setup     Install dependencies"
    echo ""
    echo "Environment variables:"
    echo "  START          Research start date (default: 2018-01-01)"
    echo "  END            Research end date (default: today)"
    echo "  POLL_INTERVAL  Seconds between polls (default: 60)"
    echo "  TICKERS        Override tickers: 'ndx=AAPL,gold=GLD,vix=^VIX,gvz=^GVZ'"
    echo "  FRED_API_KEY   FRED economic data access"
    echo "  NEWSAPI_KEY    NewsAPI sentiment scoring"
    exit 1
    ;;
esac
