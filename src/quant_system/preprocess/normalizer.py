"""
Normalization utilities: returns computation and value scaling.

These operate on plain pandas Series/DataFrames so they're usable
both here (on price bars) and later in 05_factors (on factor values).
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


class Normalizer:
    """Stateless normalization helpers."""

    @staticmethod
    def simple_returns(prices: pd.Series) -> pd.Series:
        """Period-over-period simple return: (p_t / p_{t-1}) - 1."""
        return prices.pct_change()

    @staticmethod
    def log_returns(prices: pd.Series) -> pd.Series:
        """Period-over-period log return: ln(p_t / p_{t-1})."""
        return np.log(prices / prices.shift(1))

    @staticmethod
    def zscore(
        series: pd.Series,
        window: Optional[int] = None,
    ) -> pd.Series:
        """
        Standardize to zero mean / unit variance. If `window` is
        given, uses a rolling window (for time-series factors);
        otherwise uses the full-sample mean/std (for cross-sectional
        factors, where `series` is one snapshot across symbols).
        """

        if window is not None:
            mean = series.rolling(window=window, min_periods=window // 2).mean()
            std = series.rolling(window=window, min_periods=window // 2).std()
        else:
            mean = series.mean()
            std = series.std()

        return (series - mean) / std.replace(0, np.nan) if hasattr(std, "replace") else (
            (series - mean) / std if std else series * 0.0
        )

    @staticmethod
    def robust_zscore(
        series: pd.Series,
        window: Optional[int] = None,
    ) -> pd.Series:
        """
        Median / MAD based standardization - less sensitive to
        outliers than zscore(). MAD is scaled by 1.4826 so it's
        comparable to a standard deviation under normality.
        """

        if window is not None:
            median = series.rolling(window=window, min_periods=window // 2).median()
            abs_dev = (series - median).abs()
            mad = abs_dev.rolling(window=window, min_periods=window // 2).median()
        else:
            median = series.median()
            mad = (series - median).abs().median()

        scaled_mad = mad * 1.4826

        if hasattr(scaled_mad, "replace"):
            scaled_mad = scaled_mad.replace(0, np.nan)
        elif scaled_mad == 0:
            return series * 0.0

        return (series - median) / scaled_mad

    @staticmethod
    def minmax(
        series: pd.Series,
        window: Optional[int] = None,
        feature_range: tuple[float, float] = (0.0, 1.0),
    ) -> pd.Series:
        """Scale to a fixed range, default [0, 1]."""

        low, high = feature_range

        if window is not None:
            series_min = series.rolling(window=window, min_periods=window // 2).min()
            series_max = series.rolling(window=window, min_periods=window // 2).max()
        else:
            series_min = series.min()
            series_max = series.max()

        span = series_max - series_min

        if hasattr(span, "replace"):
            span = span.replace(0, np.nan)
            scaled = (series - series_min) / span
        else:
            scaled = (series - series_min) / span if span else series * 0.0

        return scaled * (high - low) + low

    @staticmethod
    def rank_pct(series: pd.Series) -> pd.Series:
        """
        Percentile rank in [0, 1] - most useful cross-sectionally
        (ranking one factor value across many symbols at a single
        point in time), since it's robust to outliers by construction.
        """
        return series.rank(pct=True)
