"""
quant_system.core_type.enums

量化交易系统核心枚举定义。
"""

from enum import Enum


class CoreType(str, Enum):
    """系统核心模块类型。"""

    MARKET_DATA = "market_data"
    FACTOR = "factor"
    MODEL = "model"
    STRATEGY = "strategy"
    RISK = "risk"
    PORTFOLIO = "portfolio"
    EXECUTION = "execution"


class AssetType(str, Enum):
    """金融资产类型。"""

    STOCK = "stock"
    ETF = "etf"
    INDEX = "index"
    OPTION = "option"
    FUTURE = "future"
    FOREX = "forex"
    BOND = "bond"
    CASH = "cash"


class MarketType(str, Enum):
    """市场类型。"""

    US = "US"
    CN = "CN"
    HK = "HK"


class DataType(str, Enum):
    """市场数据类型。"""

    TICK = "tick"
    BAR = "bar"
    ORDER_BOOK = "order_book"
    FUNDAMENTAL = "fundamental"
    CORPORATE_ACTION = "corporate_action"


class BarInterval(str, Enum):
    """K线周期。"""

    SECOND_1 = "1s"
    SECOND_5 = "5s"
    SECOND_10 = "10s"
    SECOND_30 = "30s"

    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"

    HOUR_1 = "1h"
    DAY_1 = "1d"


class OrderSide(str, Enum):
    """订单方向。"""

    BUY = "buy"
    SELL = "sell"


class PositionSide(str, Enum):
    """持仓方向。"""

    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


class OrderType(str, Enum):
    """订单类型。"""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(str, Enum):
    """订单状态。"""

    CREATED = "created"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"

    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"

    CANCELED = "canceled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TimeInForce(str, Enum):
    """订单有效期。"""

    DAY = "day"
    GTC = "gtc"
    IOC = "ioc"
    FOK = "fok"


class SignalDirection(str, Enum):
    """交易信号方向。"""

    LONG = "long"
    SHORT = "short"
    EXIT = "exit"
    HOLD = "hold"


class SignalStrength(str, Enum):
    """信号强度。"""

    WEAK = "weak"
    NORMAL = "normal"
    STRONG = "strong"


class ModelType(str, Enum):
    """模型类型。"""

    RULE_BASED = "rule_based"
    STATISTICAL = "statistical"
    MACHINE_LEARNING = "machine_learning"
    DEEP_LEARNING = "deep_learning"


class RunMode(str, Enum):
    """系统运行模式。"""

    BACKTEST = "backtest"
    PAPER = "paper"
    LIVE = "live"