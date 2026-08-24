from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


class Direction(str, Enum):
    """买卖方向"""
    LONG = "LONG"      # 多头 / 买入
    SHORT = "SHORT"    # 空头 / 卖出


class Offset(str, Enum):
    """开平仓方向"""
    OPEN = "OPEN"        # 开仓
    CLOSE = "CLOSE"      # 平仓
    CLOSETODAY = "CLOSETODAY"  # 平今
    CLOSEYESTERDAY = "CLOSEYESTERDAY"  # 平昨


class OrderType(str, Enum):
    """订单类型"""
    LIMIT = "LIMIT"            # 限价单
    MARKET = "MARKET"          # 市价单
    STOP = "STOP"               # 止损单（触价后转市价）
    STOP_LIMIT = "STOP_LIMIT"   # 止损限价单（触价后转限价）


class OrderStatus(str, Enum):
    """
    订单状态。

    这是系统内部统一使用的状态集合，与 IBKR 原生状态
    (PendingSubmit / PreSubmitted / Submitted / Filled /
    Cancelled / Inactive 等) 不是一一对应的字符串，
    两者之间的映射逻辑应该放在
    execution/brokers/ibkr/ 的网关适配层里完成。
    """
    SUBMITTING = "SUBMITTING"  # 提交中
    NOTTRADED = "NOTTRADED"    # 未成交 (已报)
    PARTTRADED = "PARTTRADED"  # 部分成交
    ALLTRADED = "ALLTRADED"    # 全部成交
    CANCELLED = "CANCELLED"    # 已撤销
    REJECTED = "REJECTED"      # 拒单


class SecurityType(str, Enum):
    """
    IBKR 资产类别（对应 IBKR API 的 secType 字段）。
    """
    STK = "STK"    # 股票
    OPT = "OPT"    # 期权
    FUT = "FUT"    # 期货
    FOP = "FOP"    # 期货期权
    CASH = "CASH"  # 外汇


class TimeInForce(str, Enum):
    """订单有效期类型（对应 IBKR 的 tif 字段）"""
    DAY = "DAY"    # 当日有效
    GTC = "GTC"    # 撤销前有效
    IOC = "IOC"    # 立即成交剩余撤销
    FOK = "FOK"    # 全部成交或立即撤销


@dataclass
class Order:
    """订单委托数据实体"""

    # --- 合约标识 ---
    # symbol 单独不足以唯一标识期权/期货合约，必须配合
    # security_type + expiry + strike + right 一起使用；
    # 如果 IBKR 已经返回 con_id，优先以 con_id 为准。
    symbol: str                              # 标的代码 (例: "NVDA")
    security_type: SecurityType = SecurityType.STK  # 资产类别
    con_id: Optional[int] = None             # IBKR 合约唯一 ID
    exchange: str = "SMART"                  # 下单路由交易所
    currency: str = "USD"                    # 计价货币

    # 期权 / 期货专用字段，股票留空
    expiry: Optional[date] = None            # 到期日
    strike: Optional[float] = None           # 行权价（仅期权）
    right: Optional[str] = None              # "C" / "P"（仅期权）
    multiplier: Optional[float] = None       # 合约乘数（期权/期货）

    # --- 委托信息 ---
    direction: Direction = Direction.LONG    # 买卖方向
    offset: Offset = Offset.OPEN             # 开平方向
    volume: float = 0.0                      # 委托数量
    price: float = 0.0                       # 委托价格（LIMIT/STOP_LIMIT 使用）
    stop_price: Optional[float] = None       # 触发价（STOP/STOP_LIMIT 使用）
    order_type: OrderType = OrderType.LIMIT  # 订单类型
    time_in_force: TimeInForce = TimeInForce.DAY  # 订单有效期

    # --- 系统 / 策略归属 ---
    order_id: str = ""                       # 系统订单唯一ID
    strategy_id: Optional[str] = None        # 产生该订单的策略标识

    # --- IBKR 侧标识（用于撤单/改单/对账）---
    ib_order_id: Optional[int] = None        # IBKR 会话内 orderId
    perm_id: Optional[int] = None            # IBKR permId（跨会话持久）

    # --- 状态 ---
    traded_volume: float = 0.0               # 已成交数量
    status: OrderStatus = OrderStatus.SUBMITTING  # 订单状态

    create_time: datetime = field(default_factory=datetime.now)  # 创建时间
    update_time: Optional[datetime] = None                       # 最新更新时间

    def __post_init__(self) -> None:
        if self.security_type in (SecurityType.OPT, SecurityType.FOP):
            if self.strike is None or self.right is None or self.expiry is None:
                raise ValueError(
                    "OPT/FOP orders require expiry, strike, and right"
                )

            if self.right.upper() not in {"C", "P"}:
                raise ValueError("right must be 'C' or 'P'")

        if self.order_type in (OrderType.STOP, OrderType.STOP_LIMIT):
            if self.stop_price is None:
                raise ValueError(
                    "STOP/STOP_LIMIT orders require stop_price"
                )

    @property
    def is_active(self) -> bool:
        """判断订单是否处于活动状态（未终结）"""
        return self.status in {
            OrderStatus.SUBMITTING,
            OrderStatus.NOTTRADED,
            OrderStatus.PARTTRADED,
        }

    @property
    def contract_key(self) -> str:
        """
        合约唯一标识，用于跨模块（Data/Database/Execution）对齐同一份合约。

        优先使用 IBKR con_id；没有 con_id 时退化为
        symbol + security_type + expiry + strike + right 的组合。
        """
        if self.con_id is not None:
            return str(self.con_id)

        return "|".join(
            str(part)
            for part in (
                self.symbol,
                self.security_type.value,
                self.expiry or "",
                self.strike or "",
                self.right or "",
            )
        )
