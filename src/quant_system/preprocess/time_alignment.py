"""
Multi-symbol time alignment.

Cross-sectional factors and portfolio construction need every
symbol's bars indexed on the same timestamps. This module builds
that common index directly from the data provided (no dependency
on an external trading-calendar service), and reindexes each
symbol's bars onto it.
"""

from __future__ import annotations

from typing import Dict, Literal

import pandas as pd

HowT = Literal["intersection", "union"]


class TimeAligner:
    """Align multiple symbols' OHLCV bars onto a common timestamp index."""

    @staticmethod
    def build_common_index(
        bars_by_symbol: Dict[str, pd.DataFrame],
        how: HowT = "intersection",
    ) -> pd.DatetimeIndex:
        """
        Build a common DatetimeIndex across all symbols.

        `how='intersection'`: only timestamps present for every
        symbol (safest for cross-sectional factors - every symbol
        has data at every point).

        `how='union'`: every timestamp seen for any symbol (useful
        when you plan to forward-fill gaps afterwards rather than
        drop symbols with slightly different trading calendars).
        """

        if not bars_by_symbol:
            return pd.DatetimeIndex([])

        indexes = [
            pd.DatetimeIndex(df["timestamp"])
            for df in bars_by_symbol.values()
            if not df.empty
        ]

        if not indexes:
            return pd.DatetimeIndex([])

        if how == "intersection":
            common = indexes[0]
            for idx in indexes[1:]:
                common = common.intersection(idx)
        elif how == "union":
            common = indexes[0]
            for idx in indexes[1:]:
                common = common.union(idx)
        else:
            raise ValueError(f"Unsupported how: {how}")

        return common.sort_values()

    @classmethod
    def align(
        cls,
        bars_by_symbol: Dict[str, pd.DataFrame],
        how: HowT = "intersection",
    ) -> Dict[str, pd.DataFrame]:
        """
        Reindex every symbol's bars onto the common index computed by
        build_common_index(). Rows introduced by a 'union' alignment
        (timestamps a given symbol didn't originally have) are left
        as NaN - run them through missing.MissingValueHandler
        afterwards if you want them filled.
        """

        common_index = cls.build_common_index(bars_by_symbol, how=how)

        aligned: Dict[str, pd.DataFrame] = {}

        for symbol, df in bars_by_symbol.items():
            indexed = df.set_index("timestamp").reindex(common_index)
            indexed.index.name = "timestamp"
            aligned[symbol] = indexed.reset_index()

        return aligned

    @staticmethod
    def to_wide(
        bars_by_symbol: Dict[str, pd.DataFrame],
        value_column: str = "close",
    ) -> pd.DataFrame:
        """
        Reshape aligned per-symbol bars into a single wide DataFrame:
        index=timestamp, columns=symbol, values=value_column.
        Assumes bars_by_symbol is already aligned (e.g. via align()).
        """

        series_by_symbol = {}

        for symbol, df in bars_by_symbol.items():
            series_by_symbol[symbol] = df.set_index("timestamp")[value_column]

        return pd.DataFrame(series_by_symbol)
