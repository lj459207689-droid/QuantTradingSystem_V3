"""
Statistical outlier detection for OHLCV bars.

This targets bad ticks / data-vendor glitches (a single bar with a
close price 10x normal, for instance) - distinct from cleaner.py
(structural validity) and adjust.py (real price changes from splits).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class OutlierDetector:
    """
    Detect and optionally handle statistical outliers in a price
    series, based on the distribution of returns rather than raw
    price levels (so it works across different price ranges).
    """

    @staticmethod
    def detect_by_return_zscore(
        data: pd.DataFrame,
        column: str = "close",
        window: int = 20,
        threshold: float = 4.0,
    ) -> pd.Series:
        """
        Flag bars whose period return is more than `threshold`
        rolling standard deviations from the rolling mean return.

        Returns a boolean Series aligned to `data.index`, True where
        the bar looks like an outlier.
        """

        if column not in data.columns:
            raise ValueError(f"Column not found: {column}")

        returns = data[column].pct_change()

        # Baseline stats are built from the PRIOR `window` returns only
        # (shift(1) before rolling) - the point being tested must not
        # contribute to its own baseline, or a genuine spike inflates
        # its own rolling std and can dilute its z-score below the
        # detection threshold.
        prior_returns = returns.shift(1)
        rolling_mean = prior_returns.rolling(window=window, min_periods=window // 2).mean()
        rolling_std = prior_returns.rolling(window=window, min_periods=window // 2).std()

        z_scores = (returns - rolling_mean) / rolling_std

        is_outlier = z_scores.abs() > threshold

        return is_outlier.fillna(False)

    @staticmethod
    def detect_by_iqr(
        data: pd.DataFrame,
        column: str = "close",
        k: float = 3.0,
    ) -> pd.Series:
        """
        Flag bars whose period return falls outside
        [Q1 - k*IQR, Q3 + k*IQR] over the full series (non-rolling).
        Simpler / more stable than the rolling z-score for shorter
        series, at the cost of not adapting to changing volatility.
        """

        if column not in data.columns:
            raise ValueError(f"Column not found: {column}")

        returns = data[column].pct_change()

        q1 = returns.quantile(0.25)
        q3 = returns.quantile(0.75)
        iqr = q3 - q1

        lower = q1 - k * iqr
        upper = q3 + k * iqr

        is_outlier = (returns < lower) | (returns > upper)

        return is_outlier.fillna(False)

    @staticmethod
    def remove_outliers(
        data: pd.DataFrame,
        outlier_mask: pd.Series,
    ) -> pd.DataFrame:
        """Drop rows flagged True in outlier_mask."""

        return data[~outlier_mask].reset_index(drop=True)

    @staticmethod
    def interpolate_outliers(
        data: pd.DataFrame,
        outlier_mask: pd.Series,
        columns: tuple[str, ...] = ("open", "high", "low", "close"),
    ) -> pd.DataFrame:
        """
        Replace flagged rows' price columns with linear interpolation
        between neighboring valid values, instead of dropping the row
        entirely (keeps the bar/volume, fixes just the price glitch).
        """

        result = data.copy()

        for column in columns:
            series = result[column].copy()
            series[outlier_mask] = np.nan
            result[column] = series.interpolate(method="linear")

        return result
