"""Local parquet caching to avoid redundant API pulls."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from bigshort.config import CACHE_DIR


def _cache_path(key: str) -> Path:
    return CACHE_DIR / f"{key}.parquet"


def save_cache(key: str, df: pd.DataFrame) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(_cache_path(key))
    df.to_csv(CACHE_DIR / f"{key}.csv")


def load_cache(key: str) -> pd.DataFrame | None:
    path = _cache_path(key)
    if path.exists():
        return pd.read_parquet(path)
    return None
