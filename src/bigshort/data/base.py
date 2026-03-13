"""Abstract data source interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class DataSource(ABC):
    """Base class for all data connectors."""

    @abstractmethod
    def fetch(self, ticker: str, start: str, end: str | None = None) -> pd.DataFrame:
        """Fetch time-series data for *ticker* between *start* and *end*.

        Returns a DataFrame indexed by date with at minimum a 'close' column.
        """
