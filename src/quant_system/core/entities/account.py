"""
Account Entity
==============

表示交易账户的资金和权益状态。
"""

from dataclasses import dataclass


@dataclass
class Account:
    """
    交易账户实体。
    """

    account_id: str

    cash: float = 0.0
    buying_power: float = 0.0
    equity: float = 0.0

    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0

    @property
    def total_pnl(self) -> float:
        """总盈亏。"""
        return self.realized_pnl + self.unrealized_pnl
