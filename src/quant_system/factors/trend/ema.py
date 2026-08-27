"""
Exponential Moving Average (EMA) factor.
"""

from __future__ import annotations

from typing import Any

from ..base import BaseFactor
from ..state import RollingWindow


class EMA(BaseFactor):
    """Exponential Moving Average factor."""

    factor_name = "ema"
    category = "trend"
    description = "Exponential Moving Average"

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

        self._multiplier = 2.0 / (period + 1)
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

        if self._value is None:
            self._window.append(price)

            if not self._window.is_full:
                return None

            self._value = self._window.sum() / self.period
            return self._value

        self._value = (
            price * self._multiplier
            + self._value
            * (1.0 - self._multiplier)
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
        return self._value is not None

    @property
    def metadata(self) -> dict[str, Any]:

        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "period": self.period,
            "price_field": self.price_field,
            "multiplier": self._multiplier,
        }

    def __repr__(self) -> str:

        return (
            f"EMA("
            f"period={self.period}, "
            f"price_field='{self.price_field}'"
            f")"
        )
