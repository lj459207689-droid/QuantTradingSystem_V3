"""
Base interface for market data storage backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class DataStorage(ABC):
    """
    Abstract interface for market data storage.

    Storage implementations must provide methods for saving,
    loading, and checking stored market data.
    """

    @abstractmethod
    def save(
        self,
        key: str,
        data: pd.DataFrame,
    ) -> None:
        """
        Save market data.

        Parameters
        ----------
        key:
            Storage key.

        data:
            Market data to store.
        """
        raise NotImplementedError

    @abstractmethod
    def load(
        self,
        key: str,
    ) -> pd.DataFrame:
        """
        Load market data by key.
        """
        raise NotImplementedError

    @abstractmethod
    def exists(
        self,
        key: str,
    ) -> bool:
        """
        Check whether stored data exists.
        """
        raise NotImplementedError
