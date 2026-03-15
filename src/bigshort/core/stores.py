"""Parquet-backed shared data stores."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from bigshort.config import CACHE_DIR
from bigshort.core.events import FillEvent, SignalEvent, TradeProposal


class MarketStore:
    """OHLCV data keyed by (ticker, date)."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = (root or CACHE_DIR) / "market"
        self._root.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, pd.DataFrame] = {}

    def _path(self, ticker: str) -> Path:
        return self._root / f"{ticker}.parquet"

    def get(self, ticker: str, start: str | None = None, end: str | None = None) -> pd.DataFrame:
        if ticker not in self._cache:
            p = self._path(ticker)
            if p.exists():
                self._cache[ticker] = pd.read_parquet(p)
            else:
                return pd.DataFrame()
        df = self._cache[ticker]
        if start:
            df = df[df.index >= start]
        if end:
            df = df[df.index <= end]
        return df

    def append(self, ticker: str, df: pd.DataFrame) -> None:
        existing = self.get(ticker)
        if existing.empty:
            combined = df
        else:
            combined = pd.concat([existing, df])
            combined = combined[~combined.index.duplicated(keep="last")]
            combined.sort_index(inplace=True)
        self._cache[ticker] = combined
        combined.to_parquet(self._path(ticker))
        combined.to_csv(self._path(ticker).with_suffix(".csv"))

    def latest(self, ticker: str) -> pd.Series:
        df = self.get(ticker)
        if df.empty:
            return pd.Series(dtype=float)
        return df.iloc[-1]


class FeatureStore:
    """Feature time series keyed by name."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = (root or CACHE_DIR) / "features"
        self._root.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, pd.Series] = {}

    def _path(self, name: str) -> Path:
        return self._root / f"{name}.parquet"

    def put(self, name: str, series: pd.Series) -> None:
        self._cache[name] = series
        frame = series.to_frame(name)
        frame.to_parquet(self._path(name))
        frame.to_csv(self._path(name).with_suffix(".csv"))

    def get(self, name: str, start: str | None = None, end: str | None = None) -> pd.Series:
        if name not in self._cache:
            p = self._path(name)
            if p.exists():
                df = pd.read_parquet(p)
                self._cache[name] = df.iloc[:, 0]
            else:
                return pd.Series(dtype=float, name=name)
        s = self._cache[name]
        if start:
            s = s[s.index >= start]
        if end:
            s = s[s.index <= end]
        return s

    def snapshot(self, as_of: str | None = None) -> pd.DataFrame:
        """Latest row of all cached features."""
        rows = {}
        for name, s in self._cache.items():
            data = s[s.index <= as_of] if as_of else s
            if not data.empty:
                rows[name] = data.iloc[-1]
        return pd.DataFrame(rows, index=["latest"])


class SignalStore:
    """Append-only log of signals and trades."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = (root or CACHE_DIR) / "signals"
        self._root.mkdir(parents=True, exist_ok=True)
        self._signals: list[dict] = []
        self._trades: list[dict] = []

    def record_signal(self, event: SignalEvent) -> None:
        self._signals.append({
            "timestamp": event.timestamp,
            "source": event.source,
            "vote": event.vote,
            **event.signals_dict,
        })

    def record_trade(self, proposal: TradeProposal, fill: FillEvent) -> None:
        self._trades.append({
            "timestamp": fill.timestamp,
            "ticker": fill.ticker,
            "side": fill.side,
            "size": proposal.size,
            "price": fill.price,
            "slippage": fill.slippage,
            "reasoning": proposal.reasoning,
            "confidence": proposal.confidence,
        })

    def flush(self) -> None:
        if self._signals:
            df = pd.DataFrame(self._signals)
            df.to_parquet(self._root / "signals.parquet")
            df.to_csv(self._root / "signals.csv", index=False)
        if self._trades:
            df = pd.DataFrame(self._trades)
            df.to_parquet(self._root / "trades.parquet")
            df.to_csv(self._root / "trades.csv", index=False)

    def get_trades(self, n: int | None = None) -> pd.DataFrame:
        if not self._trades:
            return pd.DataFrame()
        df = pd.DataFrame(self._trades)
        if n:
            df = df.tail(n)
        return df

    def get_portfolio(self) -> dict:
        """Simple portfolio from trade log: net position per ticker."""
        positions: dict[str, float] = {}
        for t in self._trades:
            sign = 1.0 if t["side"] == "buy" else -1.0
            positions[t["ticker"]] = positions.get(t["ticker"], 0.0) + sign * t["size"]
        return positions
