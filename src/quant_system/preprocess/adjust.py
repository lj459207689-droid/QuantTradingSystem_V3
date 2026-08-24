"""
Price adjustment (复权) for splits and dividends.

Two conventions are supported:

- FORWARD (前复权): historical prices are scaled so that the most
  recent price matches today's actual traded price. Preferred for
  technical indicators / momentum factors, since "today's price" on
  the chart matches what you'd actually see quoted.
- BACKWARD (后复权): the earliest price stays as the real historical
  traded price, and later prices are scaled to keep the series
  continuous. Preferred when you care about actual historical fill
  prices (e.g. backtest P&L reconciliation).

This module is intentionally decoupled from how corporate actions
are sourced - `apply()` takes a plain DataFrame of
[timestamp, dividend, split_ratio] and does not care whether that
came from yfinance, IBKR, or a manual CSV. A convenience
`fetch_yahoo_actions()` is provided for the common case, using the
same lazy-import pattern as data.historical.yahoo so this module
stays importable without yfinance installed.

split_ratio convention: a 2-for-1 split is represented as 2.0
(you end up with 2x the shares at 1/2 the price). A ratio of 1.0
means "no split on this date".
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

import pandas as pd

PRICE_COLUMNS = ("open", "high", "low", "close")


class AdjustmentMethod(str, Enum):
    NONE = "NONE"
    FORWARD = "FORWARD"    # 前复权
    BACKWARD = "BACKWARD"  # 后复权


class PriceAdjuster:
    """
    Apply split/dividend adjustment to an OHLCV DataFrame.
    """

    @staticmethod
    def _empty_actions() -> pd.DataFrame:
        return pd.DataFrame(columns=["timestamp", "dividend", "split_ratio"])

    @classmethod
    def compute_forward_factors(
        cls,
        data: pd.DataFrame,
        corporate_actions: pd.DataFrame,
    ) -> pd.Series:
        """
        Compute a per-row multiplicative factor (aligned to `data`,
        ascending timestamp order) such that
        adjusted_price = raw_price * factor
        produces forward-adjusted (前复权) prices: the last row's
        factor is always 1.0, and factors for earlier rows shrink to
        absorb the effect of later splits/dividends.
        """

        if data.empty:
            return pd.Series(dtype=float)

        data = data.sort_values("timestamp").reset_index(drop=True)

        actions = corporate_actions if corporate_actions is not None else cls._empty_actions()
        actions_by_date = {
            pd.Timestamp(row["timestamp"]): row
            for _, row in actions.iterrows()
        }

        n = len(data)
        factors = pd.Series(1.0, index=data.index)

        cumulative = 1.0

        # Walk backward from the most recent bar. An action recorded
        # ON date t affects the adjustment of all bars STRICTLY
        # BEFORE t (the bar on the ex-date itself already reflects
        # the new, post-action price).
        for i in range(n - 1, -1, -1):
            factors.iloc[i] = cumulative

            ts = pd.Timestamp(data["timestamp"].iloc[i])
            action = actions_by_date.get(ts)

            if action is None:
                continue

            split_ratio = float(action.get("split_ratio", 1.0) or 1.0)
            dividend = float(action.get("dividend", 0.0) or 0.0)

            ratio = 1.0

            if split_ratio and split_ratio != 1.0:
                ratio *= 1.0 / split_ratio

            if dividend:
                prev_close = (
                    data["close"].iloc[i - 1] if i > 0 else data["close"].iloc[i]
                )
                if prev_close:
                    ratio *= max(0.0, (prev_close - dividend) / prev_close)

            cumulative *= ratio

        return factors

    @classmethod
    def apply(
        cls,
        data: pd.DataFrame,
        corporate_actions: Optional[pd.DataFrame] = None,
        method: AdjustmentMethod = AdjustmentMethod.FORWARD,
    ) -> pd.DataFrame:
        """
        Return a copy of `data` with OHLC columns adjusted.

        `corporate_actions` columns: [timestamp, dividend, split_ratio].
        Rows/columns may be omitted per-date (missing dividend/split
        treated as 0.0 / 1.0 respectively).
        """

        if method == AdjustmentMethod.NONE or data.empty:
            return data.copy()

        if corporate_actions is None or corporate_actions.empty:
            # Nothing to adjust for - return as-is rather than raising,
            # since "no known corporate actions" is a common, valid case.
            return data.copy()

        result = data.sort_values("timestamp").reset_index(drop=True)

        forward_factors = cls.compute_forward_factors(result, corporate_actions)

        if method == AdjustmentMethod.FORWARD:
            factors = forward_factors
        else:
            # BACKWARD: keep the earliest price fixed, scale everything
            # relative to that instead of the most recent price.
            base = forward_factors.iloc[0]
            factors = forward_factors / base if base else forward_factors

        for column in PRICE_COLUMNS:
            result[column] = result[column] * factors

        return result

    @staticmethod
    def fetch_yahoo_actions(symbol: str) -> pd.DataFrame:
        """
        Fetch dividends + splits for `symbol` from Yahoo Finance and
        return them in the [timestamp, dividend, split_ratio] shape
        `apply()` expects. Lazily imports yfinance so this module
        stays importable without it installed (same pattern as
        data.historical.yahoo.YahooHistoricalDataProvider).
        """

        try:
            import yfinance as yf
        except ImportError as exc:
            raise ImportError(
                "yfinance is required for fetch_yahoo_actions. "
                "Install it with: pip install yfinance"
            ) from exc

        ticker = yf.Ticker(symbol)
        actions = ticker.actions

        if actions is None or actions.empty:
            return pd.DataFrame(columns=["timestamp", "dividend", "split_ratio"])

        actions = actions.reset_index()
        actions.rename(
            columns={
                actions.columns[0]: "timestamp",
                "Dividends": "dividend",
                "Stock Splits": "split_ratio",
            },
            inplace=True,
        )

        actions["split_ratio"] = actions["split_ratio"].replace(0.0, 1.0)
        actions["timestamp"] = pd.to_datetime(actions["timestamp"])

        return actions[["timestamp", "dividend", "split_ratio"]]
