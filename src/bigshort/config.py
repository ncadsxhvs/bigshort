"""Settings and constants for BigShort."""

from __future__ import annotations

import os
from pathlib import Path

# Tickers
NDX_TICKER = "^NDX"
GOLD_TICKER = "GC=F"
VIX_TICKER = "^VIX"
GVZ_TICKER = "^GVZ"

# Date range defaults
DEFAULT_START = "2018-01-01"
DEFAULT_END = None  # None → today

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = PROJECT_ROOT / "data"

# Rolling window
CORRELATION_WINDOW = 60
