"""
quant_system.core_type.types

量化交易系统通用类型定义。
"""

from datetime import date, datetime
from decimal import Decimal
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    TypeVar,
    Union,
)


# ============================================================
# 基础数值类型
# ============================================================

Number = Union[int, float, Decimal]

Price = float

Quantity = float

Amount = float

Percentage = float

Probability = float


# ============================================================
# 时间类型
# ============================================================

Timestamp = datetime

Date = date


# ============================================================
# 标识符类型
# ============================================================

Symbol = str

Exchange = str

Currency = str

AccountId = str

OrderId = str

TradeId = str

PositionId = str

StrategyId = str

ModelId = str


# ============================================================
# 市场数据类型
# ============================================================

PriceSeries = Sequence[Price]

ReturnSeries = Sequence[float]

VolumeSeries = Sequence[Quantity]


# ============================================================
# 因子 / 模型类型
# ============================================================

FeatureVector = Mapping[str, float]

FactorValues = Mapping[str, float]

SignalValue = float

SignalScore = float

Confidence = float


# ============================================================
# 策略类型
# ============================================================

SignalMap = Mapping[Symbol, SignalValue]

TargetPosition = Mapping[Symbol, Quantity]

TargetWeight = Mapping[Symbol, float]


# ============================================================
# 风险类型
# ============================================================

RiskValue = float

Volatility = float

Drawdown = float

VaR = float

CVaR = float

Exposure = float

Leverage = float


# ============================================================
# 交易绩效类型
# ============================================================

Return = float

PnL = float

Commission = float

Slippage = float

Turnover = float

SharpeRatio = float

SortinoRatio = float

MaxDrawdown = float


# ============================================================
# 通用数据类型
# ============================================================

JsonValue = Union[
    str,
    int,
    float,
    bool,
    None,
    List[Any],
    Dict[str, Any],
]

JsonDict = Dict[str, JsonValue]

Metadata = Dict[str, Any]


# ============================================================
# Callable 类型
# ============================================================

T = TypeVar("T")

Factory = Callable[..., T]

Callback = Callable[..., None]

SignalGenerator = Callable[..., Mapping[Symbol, SignalValue]]

RiskChecker = Callable[..., bool]


# ============================================================
# Optional 类型
# ============================================================

OptionalPrice = Optional[Price]

OptionalQuantity = Optional[Quantity]

OptionalTimestamp = Optional[Timestamp]