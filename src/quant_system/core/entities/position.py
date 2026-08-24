from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from .order import Direction, SecurityType


@dataclass
class Position:
    """
    持仓实体 (Position)

    记录单个合约、单个方向的持仓数量、均价、未实现盈亏等。

    合约标识字段与 Order / Fill 保持一致。对于股票，
    contract_key 退化为 symbol + direction；对于期权/期货，
    必须带上 expiry/strike/right 才能唯一定位到具体合约
    （同一个标的可能同时持有多个不同行权价/到期日的期权仓位）。
    """

    # --- 合约标识 ---
    symbol: str                              # 标的代码 (如 AAPL)
    security_type: SecurityType = SecurityType.STK
    con_id: Optional[int] = None             # IBKR 合约唯一 ID
    exchange: str = "SMART"                  # 交易所
    currency: str = "USD"

    expiry: Optional[date] = None            # 到期日（仅期权/期货）
    strike: Optional[float] = None           # 行权价（仅期权）
    right: Optional[str] = None              # "C" / "P"（仅期权）
    multiplier: Optional[float] = None       # 合约乘数

    # --- 持仓信息 ---
    direction: Direction = Direction.LONG    # 持仓方向 (LONG / SHORT)
    volume: float = 0.0                      # 总持仓数量
    frozen: float = 0.0                      # 冻结数量 (挂单平仓中)
    price: float = 0.0                       # 持仓均价 (成本价)
    pnl: float = 0.0                         # 浮动盈亏 (未实现盈亏)
    realized_pnl: float = 0.0                # 已实现盈亏

    last_update: datetime = field(default_factory=datetime.now)  # 最新更新时间

    def __post_init__(self) -> None:
        if self.security_type in (SecurityType.OPT, SecurityType.FOP):
            if self.strike is None or self.right is None or self.expiry is None:
                raise ValueError(
                    "OPT/FOP positions require expiry, strike, and right"
                )

    @property
    def available(self) -> float:
        """可平仓数量 = 总持仓 - 冻结数量"""
        return self.volume - self.frozen

    @property
    def contract_key(self) -> str:
        """
        合约 + 方向的唯一标识，用于在 Portfolio.positions 字典、
        以及数据库 positions 表里做主键。

        股票场景下退化为 "SYMBOL|LONG" 这种简单组合；期权/期货
        场景下会带上到期日/行权价/right，避免同一标的的不同
        合约互相覆盖。
        """
        base = str(self.con_id) if self.con_id is not None else "|".join(
            str(part)
            for part in (
                self.symbol,
                self.security_type.value,
                self.expiry or "",
                self.strike or "",
                self.right or "",
            )
        )

        return f"{base}|{self.direction.value}"
