
"""
Bar 数据实体

定义量化交易系统中的 OHLCV K线数据结构。
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Bar:
    """
    OHLCV K线数据。

    一根 Bar 表示某一时间周期内的市场行情数据，
    例如 1秒、1分钟、5分钟、1小时或1日K线。

    Attributes
    ----------
    symbol : str
        股票或金融产品代码，例如 "NVDA"。

    timestamp : datetime
        Bar 的时间戳。

    open : float
        开盘价。

    high : float
        最高价。

    low : float
        最低价。

    close : float
        收盘价。

    volume : float
        成交量。

    vwap : float | None
        成交量加权平均价格，可为空。
    """

    symbol: str
    timestamp: datetime

    open: float
    high: float
    low: float
    close: float

    volume: float = 0.0
    vwap: float | None = None
