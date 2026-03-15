"""Settings and constants for BigShort."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Default ticker map — overridable via CLI --tickers
DEFAULT_TICKERS: dict[str, str] = {
    "ndx": "^NDX",
    "gold": "GC=F",
    "vix": "^VIX",
    "gvz": "^GVZ",
}

# Legacy aliases
NDX_TICKER = DEFAULT_TICKERS["ndx"]
GOLD_TICKER = DEFAULT_TICKERS["gold"]
VIX_TICKER = DEFAULT_TICKERS["vix"]
GVZ_TICKER = DEFAULT_TICKERS["gvz"]

# Date range defaults
DEFAULT_START = "2020-01-01"
DEFAULT_END = None  # None → today

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = PROJECT_ROOT / "data"

# Rolling window
CORRELATION_WINDOW = 60

# Agent settings
POLL_INTERVAL = 60.0         # DataAgent poll interval (seconds)
SENTIMENT_INTERVAL = 900.0   # SentimentAgent poll interval (seconds)

# HumanGate mode: "auto" | "approve" | "observe"
GATE_MODE = os.environ.get("BIGSHORT_GATE", "observe")
