"""Multi-asset time alignment utilities."""

from __future__ import annotations

import pandas as pd


def align_to_trading_calendar(
    frames: dict[str, pd.DataFrame],
    reference_key: str = "ndx",
) -> dict[str, pd.DataFrame]:
    """Align all DataFrames to the trading dates of *reference_key*.

    Missing dates are forward-filled (last observation carried forward).
    """
    ref_index = frames[reference_key].index
    aligned: dict[str, pd.DataFrame] = {}
    for key, df in frames.items():
        aligned[key] = df.reindex(ref_index).ffill()
    return aligned
