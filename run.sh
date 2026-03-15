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
    echo "Running full research pipeline..."
    python3 -m bigshort research \
      --start "${START:-2020-01-01}" \
      --end "${END:-}" \
      $TICKER_FLAG
    ;;

  # Individual stages
  data)
    echo "Fetching market data (YFinance + FRED)..."
    python3 -m bigshort research --stage data \
      --start "${START:-2020-01-01}" \
      --end "${END:-}" \
      $TICKER_FLAG
    ;;
  features)
    echo "Computing features (correlation, Kalman, MACD, vol)..."
    python3 -m bigshort research --stage features \
      --start "${START:-2020-01-01}" \
      --end "${END:-}" \
      $TICKER_FLAG
    ;;
  sentiment)
    echo "Fetching sentiment (NewsAPI, Reddit)..."
    python3 -m bigshort research --stage sentiment \
      --start "${START:-2020-01-01}" \
      --end "${END:-}" \
      $TICKER_FLAG
    ;;
  regime)
    echo "Detecting regime (HMM)..."
    python3 -m bigshort research --stage regime \
      --start "${START:-2020-01-01}" \
      --end "${END:-}" \
      $TICKER_FLAG
    ;;
  signals)
    echo "Generating signals (MACD, rotation, straddle, voting)..."
    python3 -m bigshort research --stage signals \
      --start "${START:-2020-01-01}" \
      --end "${END:-}" \
      $TICKER_FLAG
    ;;
  strategies)
    echo "Running strategies + execution..."
    python3 -m bigshort research --stage strategies \
      --start "${START:-2020-01-01}" \
      --end "${END:-}" \
      $TICKER_FLAG
    ;;

  # Backtest a single ticker
  backtest)
    TICKER="${2:?Usage: ./run.sh backtest <TICKER> [years]}"
    YEARS="${3:-3}"
    echo "Backtesting ${TICKER} over ${YEARS} years..."
    python3 -m bigshort backtest "$TICKER" \
      --years "$YEARS" \
      --slippage "${SLIPPAGE:-5}"
    ;;

  # Live modes
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

  # Utilities
  test)
    echo "Running tests..."
    python3 -m pytest tests/ -v
    ;;
  setup)
    echo "Installing bigshort..."
    python3 -m pip install -e ".[dev]"
    ;;
  *)
    echo "Usage: ./run.sh <command>"
    echo ""
    echo "Full pipeline:"
    echo "  research              Run all stages end-to-end (default)"
    echo "  backtest <TICKER> [y] Backtest a ticker (default: 3 years)"
    echo ""
    echo "Individual stages:"
    echo "  data        Fetch market data (YFinance + FRED)"
    echo "  features    Compute technical features"
    echo "  sentiment   Fetch sentiment scores"
    echo "  regime      Detect market regime (HMM)"
    echo "  signals     Generate trading signals + voting"
    echo "  strategies  Run strategies + execution sim"
    echo ""
    echo "Live modes:"
    echo "  paper       Paper trading with simulated execution"
    echo "  live        Live trading with human approval"
    echo ""
    echo "Utilities:"
    echo "  test        Run test suite"
    echo "  setup       Install dependencies"
    echo ""
    echo "Environment variables:"
    echo "  START          Start date (default: 2020-01-01)"
    echo "  END            End date (default: today)"
    echo "  POLL_INTERVAL  Seconds between polls (default: 60)"
    echo "  TICKERS        Override tickers: 'ndx=AAPL,gold=GLD'"
    echo "  FRED_API_KEY   FRED economic data access"
    echo "  NEWSAPI_KEY    NewsAPI sentiment scoring"
    exit 1
    ;;
esac
