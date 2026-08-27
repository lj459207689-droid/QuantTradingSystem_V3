"""
Interactive Brokers historical market data provider.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from .base import HistoricalDataProvider


class IBKRHistoricalDataProvider(HistoricalDataProvider):
    """
    Historical market data provider for Interactive Brokers.

    The IB connection is injected from outside.
    """

    def __init__(
        self,
        ib=None,
        exchange: str = "SMART",
        currency: str = "USD",
    ) -> None:

        self.ib = ib
        self.exchange = exchange
        self.currency = currency
        self.name = "ibkr"

    def set_connection(self, ib) -> None:
        """
        Inject an existing IBKR connection.
        """
        self.ib = ib

    def _require_connection(self) -> None:
        """
        Ensure an IBKR connection exists and is connected.
        """

        if self.ib is None:
            raise RuntimeError(
                "IBKR connection is not configured."
            )

        if hasattr(self.ib, "isConnected"):

            if not self.ib.isConnected():
                raise RuntimeError(
                    "IBKR connection is not connected."
                )

    def get_bars(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Retrieve historical OHLCV bars from IBKR.
        """

        self.validate(
            symbol,
            start,
            end,
            interval,
        )

        self._require_connection()

        try:
            from ib_insync import Stock

        except ImportError as exc:

            raise ImportError(
                "ib_insync is required for IBKR "
                "historical data. "
                "Install it with: pip install ib_insync"
            ) from exc

        contract = Stock(
            symbol,
            self.exchange,
            self.currency,
        )

        duration = self._calculate_duration(
            start,
            end,
        )

        bars = self.ib.reqHistoricalData(
            contract,
            endDateTime=end,
            durationStr=duration,
            barSizeSetting=self._convert_interval(
                interval
            ),
            whatToShow="TRADES",
            useRTH=False,
            formatDate=1,
            keepUpToDate=False,
        )

        if not bars:

            return pd.DataFrame(
                columns=[
                    "timestamp",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                ]
            )

        rows = []

        for bar in bars:

            rows.append(
                {
                    "timestamp": bar.date,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                }
            )

        return self.normalize_dataframe(
            pd.DataFrame(rows)
        )

    @staticmethod
    def _convert_interval(
        interval: str,
    ) -> str:
        """
        Convert system interval notation to IBKR notation.
        """

        mapping = {
            "1s": "1 secs",
            "5s": "5 secs",
            "10s": "10 secs",
            "15s": "15 secs",
            "30s": "30 secs",
            "1m": "1 min",
            "5m": "5 mins",
            "15m": "15 mins",
            "30m": "30 mins",
            "1h": "1 hour",
            "1d": "1 day",
        }

        if interval not in mapping:

            raise ValueError(
                f"Unsupported IBKR interval: {interval}"
            )

        return mapping[interval]

    @staticmethod
    def _calculate_duration(
        start: datetime,
        end: datetime,
    ) -> str:
        """
        Convert date range to an IBKR duration string.
        """

        seconds = int(
            (end - start).total_seconds()
        )

        days = max(
            1,
            seconds // 86400,
        )

        if days <= 30:
            return f"{days} D"

        months = max(
            1,
            days // 30,
        )

        if months <= 12:
            return f"{months} M"

        years = max(
            1,
            days // 365,
        )

        return f"{years} Y"
