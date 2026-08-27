"""
Central DataManager for the quantitative trading system.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import pandas as pd

from .historical.base import HistoricalDataProvider
from .historical.ibkr import IBKRHistoricalDataProvider
from .historical.yahoo import YahooHistoricalDataProvider
from .realtime.base import RealtimeDataProvider
from .realtime.ibkr import IBKRRealtimeDataProvider
from .storage.base import DataStorage
from .storage.parquet import ParquetStorage


class DataManager:
    """
    Central manager for all market data operations.

    Responsibilities
    ----------------
    - Historical data
    - Realtime data
    - Storage
    - Provider selection
    """

    def __init__(
        self,
        ib=None,
        storage: Optional[DataStorage] = None,
        historical_provider: str = "yahoo",
    ) -> None:

        self.ib = ib

        self.storage = (
            storage
            if storage is not None
            else ParquetStorage("data")
        )

        self.historical_providers = {
            "yahoo": YahooHistoricalDataProvider(),
            "ibkr": IBKRHistoricalDataProvider(
                ib=ib
            ),
        }

        self.realtime_providers = {
            "ibkr": IBKRRealtimeDataProvider(
                ib=ib
            ),
        }

        if historical_provider not in self.historical_providers:
            raise ValueError(
                f"Unsupported historical provider: "
                f"{historical_provider}"
            )

        self.historical_provider_name = (
            historical_provider
        )

    @property
    def historical(self) -> HistoricalDataProvider:
        """Return the currently selected historical provider."""
        return self.historical_providers[
            self.historical_provider_name
        ]

    @property
    def realtime(self) -> RealtimeDataProvider:
        """Return the IBKR realtime provider."""
        return self.realtime_providers["ibkr"]

    def set_historical_provider(
        self,
        name: str,
    ) -> None:
        """Select a historical data provider."""

        if name not in self.historical_providers:
            raise ValueError(
                f"Unknown historical provider: {name}"
            )

        self.historical_provider_name = name

    def get_bars(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "1d",
        provider: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Retrieve historical bars.
        """

        if provider is not None:
            self.set_historical_provider(provider)

        return self.historical.get_bars(
            symbol=symbol,
            start=start,
            end=end,
            interval=interval,
        )

    def save(
        self,
        key: str,
        data: pd.DataFrame,
    ) -> None:
        """Save market data."""

        self.storage.save(
            key,
            data,
        )

    def load(
        self,
        key: str,
    ) -> pd.DataFrame:
        """Load market data."""

        return self.storage.load(key)

    def storage_exists(
        self,
        key: str,
    ) -> bool:
        """Check whether stored data exists."""

        return self.storage.exists(key)

    def providers(self) -> dict:
        """Return available data providers."""

        return {
            "historical": list(
                self.historical_providers.keys()
            ),
            "realtime": list(
                self.realtime_providers.keys()
            ),
        }
