"""
Trade Entity
============

表示一笔已经完成的交易记录。
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Trade:
    """
    交易记录实体。
    """

    trade_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    timestamp: datetime

    commission: float = 0.0
    realized_pnl: float = 0.0
    order_id: Optional[str] = None

    @property
    def notional_value(self) -> float:
        """交易名义价值。"""
        return self.quantity * self.price
