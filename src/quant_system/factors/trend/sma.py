"""
Simple Moving Average (SMA) factor.
"""
from __future__ import annotations

from typing import Any

from ..base import BaseFactor
from ..state import RollingWindow


class SMA(BaseFactor):
    """Simple Moving Average factor."""

    factor_name = "sma"
    category = "trend"
    description = "Simple Moving Average"

    def __init__(
        self,
        period: int = 20,
        price_field: str = "close",
    ) -> None:
        if not isinstance(period, int):
            raise TypeError("period must be an integer")
        if period <= 0:
            raise ValueError(
                "period must be greater than zero"
            )
        self.period = period
        self.price_field = price_field
        self._window = RollingWindow(period)
        self._value: float | None = None

    @property
    def name(self) -> str:
        return f"{self.factor_name}_{self.period}"

    def _extract_price(self, data: Any) -> float:
        if isinstance(data, (int, float)):
            return float(data)

        if isinstance(data, dict):
            if self.price_field not in data:
                raise ValueError(
                    f"Missing price field: {self.price_field}"
                )
            return float(data[self.price_field])

        if hasattr(data, self.price_field):
            return float(
                getattr(data, self.price_field)
            )

        try:
            return float(data[self.price_field])
        except (KeyError, TypeError, IndexError):
            raise ValueError(
                f"Cannot find price field "
                f"'{self.price_field}'"
            )

    def update(self, data: Any) -> float | None:
        price = self._extract_price(data)
        self._window.append(price)

        if not self._window.is_full:
            self._value = None
            return None

        self._value = (
            self._window.sum()
            / self.period
        )
        return self._value

    def reset(self) -> None:
        self._window.clear()
        self._value = None

    @property
    def value(self) -> float | None:
        return self._value

    @property
    def is_ready(self) -> bool:
        return self._window.is_full

    @property
    def metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "period": self.period,
            "price_field": self.price_field,
        }

    def __repr__(self) -> str:
        return (
            f"SMA("
            f"period={self.period}, "
            f"price_field='{self.price_field}'"
            f")"
        )
