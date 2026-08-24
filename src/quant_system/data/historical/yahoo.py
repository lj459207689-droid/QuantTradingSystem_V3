"""
Yahoo Finance historical data provider.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from .base import HistoricalDataProvider


class YahooHistoricalDataProvider(HistoricalDataProvider):
    """
    Historical data provider based on Yahoo Finance.

    This provider imports yfinance lazily so that the core
    Data module can still be imported when yfinance is absent.
    """

    def __init__(self) -> None:
        self.name = "yahoo"

    def get_bars(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "1d",
    ) -> pd.DataFrame:

        self.validate(symbol, start, end, interval)

        try:
            import yfinance as yf
        except ImportError as exc:
            raise ImportError(
                "yfinance is required for YahooHistoricalDataProvider. "
                "Install it with: pip install yfinance"
            ) from exc

        data = yf.download(
            symbol,
            start=start,
            end=end,
            interval=interval,
            auto_adjust=False,
            progress=False,
        )

        if data is None or data.empty:
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

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [column[0] for column in data.columns]

        data = data.reset_index()

        timestamp_column = "Datetime"

        if timestamp_column not in data.columns:
            timestamp_column = "Date"

        data.rename(
            columns={
                timestamp_column: "timestamp",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            },
            inplace=True,
        )

        return self.normalize_dataframe(data)
