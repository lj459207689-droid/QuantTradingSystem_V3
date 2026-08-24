from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from .order import Direction, Offset, SecurityType


@dataclass
class Fill:
    """
    成交回报数据实体（原 Trade 实体）。

    一笔订单可能对应多条 Fill（部分成交多次）。合约标识字段
    与 Order 保持一致，便于按 contract_key 把 Fill 和它所属的
    Order 精确对齐，尤其是期权/期货场景。
    """

    # --- 合约标识（与 Order 对齐）---
    symbol: str                              # 标的代码
    security_type: SecurityType = SecurityType.STK
    con_id: Optional[int] = None             # IBKR 合约唯一 ID
    exchange: str = "SMART"
    currency: str = "USD"

    expiry: Optional[date] = None            # 到期日（仅期权/期货）
    strike: Optional[float] = None           # 行权价（仅期权）
    right: Optional[str] = None              # "C" / "P"（仅期权）
    multiplier: Optional[float] = None       # 合约乘数

    # --- 成交信息 ---
    order_id: str = ""                       # 关联的系统订单ID
    fill_id: str = ""                        # 成交记录唯一ID（系统生成）
    ib_exec_id: Optional[str] = None         # IBKR 原生 execId，用于去重
    direction: Direction = Direction.LONG    # 成交方向
    offset: Offset = Offset.OPEN             # 开平方向
    price: float = 0.0                       # 成交价格
    volume: float = 0.0                      # 本次成交数量
    commission: float = 0.0                  # 成交手续费
    fill_time: datetime = field(default_factory=datetime.now)  # 成交时间

    def __post_init__(self) -> None:
        if self.security_type in (SecurityType.OPT, SecurityType.FOP):
            if self.strike is None or self.right is None or self.expiry is None:
                raise ValueError(
                    "OPT/FOP fills require expiry, strike, and right"
                )

    @property
    def contract_key(self) -> str:
        """合约唯一标识，逻辑与 Order.contract_key 保持一致。"""

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

    @property
    def notional_value(self) -> float:
        """成交名义价值（不含合约乘数）。"""
        return self.price * self.volume
