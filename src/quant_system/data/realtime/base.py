"""
Base interface for realtime market data providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional


class RealtimeDataProvider(ABC):
    """
    Realtime market data provider interface.

    All realtime data providers must implement this interface.
    """

    @abstractmethod
    def subscribe(
        self,
        symbol: str,
        callback: Optional[Callable[[Any], None]] = None,
    ) -> None:
        """
        Subscribe to realtime market data.

        Parameters
        ----------
        symbol:
            Trading symbol.

        callback:
            Optional callback invoked when new market data arrives.
        """
        raise NotImplementedError

    @abstractmethod
    def unsubscribe(
        self,
        symbol: str,
    ) -> None:
        """
        Unsubscribe from realtime market data.
        """
        raise NotImplementedError

    @abstractmethod
    def get_latest(
        self,
        symbol: str,
    ) -> Any:
        """
        Return the latest realtime market data for a symbol.
        """
        raise NotImplementedError
