"""
Interactive Brokers realtime market data provider.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from .base import RealtimeDataProvider


class IBKRRealtimeDataProvider(RealtimeDataProvider):
    """
    Realtime market data provider for Interactive Brokers.

    The IBKR client is injected from outside so that connection
    management remains separate from market-data management.
    """

    def __init__(
        self,
        ib=None,
    ) -> None:
        """
        Initialize the IBKR realtime provider.

        Parameters
        ----------
        ib:
            Optional IBKR client instance.
        """

        self._ib = ib
        self._subscriptions: dict[
            str,
            Callable[[Any], None] | None,
        ] = {}

        self._latest: dict[str, Any] = {}

    @property
    def ib(self):
        """Return the configured IBKR client."""

        return self._ib

    def subscribe(
        self,
        symbol: str,
        callback: Optional[Callable[[Any], None]] = None,
    ) -> None:
        """
        Subscribe to realtime market data.

        The actual IBKR market-data request will be implemented
        in the next stage.
        """

        if not symbol:
            raise ValueError(
                "symbol must not be empty"
            )

        self._subscriptions[symbol] = callback

        if self._ib is None:
            raise RuntimeError(
                "IBKR client is not configured"
            )

        raise NotImplementedError(
            "IBKR realtime subscription is not implemented yet"
        )

    def unsubscribe(
        self,
        symbol: str,
    ) -> None:
        """
        Unsubscribe from realtime market data.
        """

        if not symbol:
            raise ValueError(
                "symbol must not be empty"
            )

        self._subscriptions.pop(
            symbol,
            None,
        )

        self._latest.pop(
            symbol,
            None,
        )

    def get_latest(
        self,
        symbol: str,
    ) -> Any:
        """
        Return the latest realtime market data.
        """

        if not symbol:
            raise ValueError(
                "symbol must not be empty"
            )

        return self._latest.get(symbol)
