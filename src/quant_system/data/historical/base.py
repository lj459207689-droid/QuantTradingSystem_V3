"""
Base interface for historical market data providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

import pandas as pd


class HistoricalDataProvider(ABC):
    """
    Historical market data provider interface.

    All historical data providers must implement this interface.
    """

    @abstractmethod
    def get_bars(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Retrieve historical OHLCV bars.

        Returns
        -------
        pandas.DataFrame
            Columns:

            timestamp
            open
            high
            low
            close
            volume
        """
        raise NotImplementedError

    def validate(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str,
    ) -> None:
        """Validate common historical data parameters."""

        if not symbol:
            raise ValueError(
                "symbol must not be empty"
            )

        if start >= end:
            raise ValueError(
                "start must be earlier than end"
            )

        if not interval:
            raise ValueError(
                "interval must not be empty"
            )

    @staticmethod
    def normalize_dataframe(
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Normalize a historical OHLCV DataFrame.
        """

        if data is None:
            raise ValueError(
                "data must not be None"
            )

        columns = [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]

        if data.empty:
            return pd.DataFrame(
                columns=columns
            )

        result = data.copy()

        result.columns = [
            str(column).lower().strip()
            for column in result.columns
        ]

        if "timestamp" not in result.columns:

            if isinstance(
                result.index,
                pd.DatetimeIndex,
            ):
                result = result.reset_index()

                result.rename(
                    columns={
                        result.columns[0]:
                            "timestamp"
                    },
                    inplace=True,
                )

            else:
                raise ValueError(
                    "historical data must contain "
                    "timestamp"
                )

        for column in [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]:
            if column not in result.columns:
                result[column] = None

        result["timestamp"] = pd.to_datetime(
            result["timestamp"],
            utc=True,
            errors="coerce",
        )

        result = result[
            columns
        ]

        result = result.dropna(
            subset=["timestamp"]
        )

        result = result.sort_values(
            "timestamp"
        )

        result = result.drop_duplicates(
            subset=["timestamp"],
            keep="last",
        )

        return result.reset_index(
            drop=True
        )