"""
Missing value / gap handling for OHLCV bars.
"""

from __future__ import annotations

from datetime import date as date_type
from typing import TYPE_CHECKING, List, Optional

import pandas as pd

if TYPE_CHECKING:
    from quant_system.common.calendar import TradingCalendar


class MissingValueHandler:
    """
    Detect and fill gaps in a single symbol's OHLCV bar series.

    All methods expect data already sorted ascending by timestamp
    (DataCleaner.clean() guarantees this).

    Two families of methods are provided:

    - find_gaps() / reindex_to_frequency(): use a naive pandas `freq`
      string (e.g. '1D'). Fine for intraday bars, but for DAILY bars
      this treats weekends (and any holidays) as "missing" trading
      days, which is wrong for equities/options that don't trade on
      those days.
    - find_gaps_calendar() / reindex_to_calendar(): use a real
      common.calendar.TradingCalendar, so weekends and configured
      holidays are correctly excluded from the expected grid. Prefer
      these for daily bars whenever a calendar is available.
    """

    @staticmethod
    def find_gaps(
        data: pd.DataFrame,
        freq: str,
    ) -> pd.DatetimeIndex:
        """
        Return timestamps that are missing relative to a regular
        `freq` grid spanning [data.timestamp.min(), data.timestamp.max()].

        `freq` uses pandas offset aliases, e.g. '1D', '1H', '5min'.
        """

        if data.empty:
            return pd.DatetimeIndex([])

        full_range = pd.date_range(
            start=data["timestamp"].min(),
            end=data["timestamp"].max(),
            freq=freq,
        )

        existing = pd.DatetimeIndex(data["timestamp"])

        return full_range.difference(existing)

    @staticmethod
    def reindex_to_frequency(
        data: pd.DataFrame,
        freq: str,
    ) -> pd.DataFrame:
        """
        Reindex onto a regular `freq` grid. Newly introduced rows have
        NaN OHLCV - use forward_fill_prices() afterwards to fill them.
        """

        if data.empty:
            return data.copy()

        full_range = pd.date_range(
            start=data["timestamp"].min(),
            end=data["timestamp"].max(),
            freq=freq,
        )

        indexed = data.set_index("timestamp").reindex(full_range)
        indexed.index.name = "timestamp"

        return indexed.reset_index()

    @staticmethod
    def forward_fill_prices(data: pd.DataFrame) -> pd.DataFrame:
        """
        Fill gaps introduced by reindex_to_frequency(): OHLC all take
        the last known close (a flat/no-trade bar), volume becomes 0.
        Leading NaNs (before the first real bar) are left as NaN.
        """

        result = data.copy()

        last_close = result["close"].ffill()

        for column in ["open", "high", "low", "close"]:
            was_missing = result[column].isna()
            result.loc[was_missing, column] = last_close[was_missing]

        result["volume"] = result["volume"].fillna(0)

        return result

    @staticmethod
    def missing_ratio(data: pd.DataFrame, freq: str) -> float:
        """Fraction of expected bars (on a `freq` grid) that are absent."""

        if data.empty:
            return 1.0

        full_range = pd.date_range(
            start=data["timestamp"].min(),
            end=data["timestamp"].max(),
            freq=freq,
        )

        if len(full_range) == 0:
            return 0.0

        existing = pd.DatetimeIndex(data["timestamp"])
        missing = full_range.difference(existing)

        return len(missing) / len(full_range)

    @classmethod
    def drop_if_missing_ratio_exceeds(
        cls,
        data: pd.DataFrame,
        freq: str,
        threshold: float,
    ) -> Optional[pd.DataFrame]:
        """
        Return None if the series is too sparse to be usable (missing
        ratio over `threshold`), otherwise return data unchanged.
        Useful as a pre-check before spending time filling gaps.
        """

        if cls.missing_ratio(data, freq) > threshold:
            return None

        return data

    # -----------------------------------------------------------------
    # Calendar-aware variants (preferred for daily bars)
    # -----------------------------------------------------------------

    @staticmethod
    def find_gaps_calendar(
        data: pd.DataFrame,
        calendar: "TradingCalendar",
    ) -> List[date_type]:
        """
        Trading days (per `calendar`, so weekends/holidays already
        excluded) between the series' min and max timestamp that have
        no bar. For daily bars, this is what find_gaps() should have
        been - it won't flag weekends as gaps.
        """

        if data.empty:
            return []

        start = pd.Timestamp(data["timestamp"].min()).date()
        end = pd.Timestamp(data["timestamp"].max()).date()

        expected = set(calendar.trading_days(start, end))
        existing = {pd.Timestamp(ts).date() for ts in data["timestamp"]}

        return sorted(expected - existing)

    @staticmethod
    def reindex_to_calendar(
        data: pd.DataFrame,
        calendar: "TradingCalendar",
    ) -> pd.DataFrame:
        """
        Reindex daily bars onto the real trading-day calendar (not a
        naive '1D' grid). Newly introduced rows have NaN OHLCV - use
        forward_fill_prices() afterwards to fill them.
        """

        if data.empty:
            return data.copy()

        start = pd.Timestamp(data["timestamp"].min()).date()
        end = pd.Timestamp(data["timestamp"].max()).date()

        trading_days = calendar.trading_days(start, end)
        full_index = pd.DatetimeIndex(
            [pd.Timestamp(d) for d in trading_days]
        )

        indexed = data.set_index("timestamp").reindex(full_index)
        indexed.index.name = "timestamp"

        return indexed.reset_index()

    @classmethod
    def missing_ratio_calendar(
        cls,
        data: pd.DataFrame,
        calendar: "TradingCalendar",
    ) -> float:
        """Fraction of expected (calendar) trading days that are absent."""

        if data.empty:
            return 1.0

        start = pd.Timestamp(data["timestamp"].min()).date()
        end = pd.Timestamp(data["timestamp"].max()).date()

        expected = calendar.trading_days(start, end)

        if not expected:
            return 0.0

        missing = cls.find_gaps_calendar(data, calendar)

        return len(missing) / len(expected)
