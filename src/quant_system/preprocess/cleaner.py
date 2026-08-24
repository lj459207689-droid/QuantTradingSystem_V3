"""
Bar data cleaning utilities.

Operates on the standard OHLCV DataFrame shape produced by
data.historical.base.HistoricalDataProvider.normalize_dataframe():
columns = [timestamp, open, high, low, close, volume].
"""

from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


class DataCleaner:
    """
    Structural / sanity cleaning for OHLCV bars.

    This does NOT handle missing timestamps (see missing.py) or
    statistical outliers (see outlier.py) - it only removes rows
    that are structurally invalid (e.g. high < low) or duplicated.
    """

    @staticmethod
    def _require_columns(data: pd.DataFrame) -> None:
        missing = [c for c in REQUIRED_COLUMNS if c not in data.columns]

        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    @classmethod
    def validity_mask(cls, data: pd.DataFrame) -> pd.Series:
        """
        Return a boolean Series, True where the row is structurally
        valid: prices positive, high is the max, low is the min,
        volume non-negative, no NaNs in required columns.
        """

        cls._require_columns(data)

        if data.empty:
            return pd.Series([], dtype=bool)

        no_na = data[REQUIRED_COLUMNS].notna().all(axis=1)

        positive_prices = (
            (data["open"] > 0)
            & (data["high"] > 0)
            & (data["low"] > 0)
            & (data["close"] > 0)
        )

        non_negative_volume = data["volume"] >= 0

        high_is_max = data["high"] >= data[["open", "close", "low"]].max(axis=1)
        low_is_min = data["low"] <= data[["open", "close", "high"]].min(axis=1)

        return (
            no_na
            & positive_prices
            & non_negative_volume
            & high_is_max
            & low_is_min
        )

    @classmethod
    def drop_invalid_ohlc(cls, data: pd.DataFrame) -> pd.DataFrame:
        """Drop rows that fail validity_mask()."""

        mask = cls.validity_mask(data)
        return data[mask].reset_index(drop=True)

    @classmethod
    def drop_duplicate_timestamps(
        cls,
        data: pd.DataFrame,
        keep: str = "last",
    ) -> pd.DataFrame:
        """Drop duplicate timestamps, keeping the first/last occurrence."""

        cls._require_columns(data)

        result = data.drop_duplicates(subset=["timestamp"], keep=keep)
        return result.sort_values("timestamp").reset_index(drop=True)

    @classmethod
    def clean(
        cls,
        data: pd.DataFrame,
        drop_invalid: bool = True,
        dedup: bool = True,
    ) -> pd.DataFrame:
        """
        Run the standard cleaning sequence: dedup, then drop
        structurally invalid rows.
        """

        cls._require_columns(data)

        result = data.copy()

        if dedup:
            result = cls.drop_duplicate_timestamps(result)

        if drop_invalid:
            result = cls.drop_invalid_ohlc(result)

        return result.reset_index(drop=True)
