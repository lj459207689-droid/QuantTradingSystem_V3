from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Tick:
    """
    Tick 行情数据实体。

    用于描述某一时刻某个交易标的的最新成交、
    买一卖一报价以及成交量信息。
    """

    timestamp: datetime
    symbol: str

    # 最新成交
    last_price: float | None = None
    last_size: float | None = None

    # 买一
    bid_price: float | None = None
    bid_size: float | None = None

    # 卖一
    ask_price: float | None = None
    ask_size: float | None = None

    # 累计成交量
    volume: float | None = None

    # 数据来源
    source: str | None = None

    @property
    def mid_price(self) -> float | None:
        """计算买卖中间价。"""
        if self.bid_price is None or self.ask_price is None:
            return None

        return (self.bid_price + self.ask_price) / 2

    @property
    def spread(self) -> float | None:
        """计算买卖价差。"""
        if self.bid_price is None or self.ask_price is None:
            return None

        return self.ask_price - self.bid_price

    @property
    def spread_bps(self) -> float | None:
        """计算买卖价差，以基点表示。"""
        mid = self.mid_price
        spread = self.spread

        if mid is None or spread is None or mid == 0:
            return None

        return spread / mid * 10_000

    @property
    def order_imbalance(self) -> float | None:
        """
        计算买卖盘不平衡度。

        OI = (BidSize - AskSize) / (BidSize + AskSize)
        """
        if self.bid_size is None or self.ask_size is None:
            return None

        total_size = self.bid_size + self.ask_size

        if total_size == 0:
            return None

        return (self.bid_size - self.ask_size) / total_size
