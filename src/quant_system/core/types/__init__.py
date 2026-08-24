"""
quant_system.core_type

量化交易系统核心类型模块。

本模块只负责：
1. 枚举定义
2. 类型别名
3. 基础通用类型

不包含具体业务逻辑。
"""

from .enums import (
    AssetType,
    BarInterval,
    CoreType,
    DataType,
    MarketType,
    ModelType,
    OrderSide,
    OrderStatus,
    OrderType,
    PositionSide,
    RunMode,
    SignalDirection,
    SignalStrength,
    TimeInForce,
)

from .types import (
    AccountId,
    Amount,
    Callback,
    Commission,
    Confidence,
    Currency,
    Date,
    Drawdown,
    Exchange,
    Exposure,
    Factory,
    FactorValues,
    FeatureVector,
    JsonDict,
    Leverage,
    MaxDrawdown,
    Metadata,
    ModelId,
    Number,
    OrderId,
    Percentage,
    PnL,
    PositionId,
    Price,
    PriceSeries,
    Probability,
    Quantity,
    Return,
    ReturnSeries,
    RiskValue,
    SharpeRatio,
    SignalGenerator,
    SignalMap,
    SignalScore,
    SignalValue,
    Slippage,
    StrategyId,
    Symbol,
    TargetPosition,
    TargetWeight,
    Timestamp,
    TradeId,
    Turnover,
    VaR,
    Volatility,
)


__all__ = [

    # ========================================================
    # Core
    # ========================================================

    "CoreType",

    # ========================================================
    # Market
    # ========================================================

    "AssetType",
    "MarketType",
    "DataType",
    "BarInterval",

    # ========================================================
    # Trading
    # ========================================================

    "OrderSide",
    "PositionSide",
    "OrderType",
    "OrderStatus",
    "TimeInForce",

    # ========================================================
    # Signal
    # ========================================================

    "SignalDirection",
    "SignalStrength",

    # ========================================================
    # Model
    # ========================================================

    "ModelType",

    # ========================================================
    # System
    # ========================================================

    "RunMode",

    # ========================================================
    # Basic types
    # ========================================================

    "Number",
    "Price",
    "Quantity",
    "Amount",
    "Percentage",
    "Probability",

    # ========================================================
    # Time
    # ========================================================

    "Timestamp",
    "Date",

    # ========================================================
    # IDs
    # ========================================================

    "Symbol",
    "Exchange",
    "Currency",
    "AccountId",
    "OrderId",
    "TradeId",
    "PositionId",
    "StrategyId",
    "ModelId",

    # ========================================================
    # Market data
    # ========================================================

    "PriceSeries",
    "ReturnSeries",

    # ========================================================
    # Factor / Model
    # ========================================================

    "FeatureVector",
    "FactorValues",
    "SignalValue",
    "SignalScore",
    "Confidence",

    # ========================================================
    # Strategy
    # ========================================================

    "SignalMap",
    "TargetPosition",
    "TargetWeight",

    # ========================================================
    # Risk
    # ========================================================

    "RiskValue",
    "Volatility",
    "Drawdown",
    "VaR",
    "Exposure",
    "Leverage",

    # ========================================================
    # Performance
    # ========================================================

    "Return",
    "PnL",
    "Commission",
    "Slippage",
    "Turnover",
    "SharpeRatio",
    "MaxDrawdown",

    # ========================================================
    # Generic
    # ========================================================

    "JsonDict",
    "Metadata",
    "Factory",
    "Callback",
    "SignalGenerator",
]