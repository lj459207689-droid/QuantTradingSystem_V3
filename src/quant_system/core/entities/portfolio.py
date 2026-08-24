from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

from .position import Position


@dataclass
class Portfolio:
    """
    账户资产组合实体。

    positions 的 key 统一使用 Position.contract_key（不再是手写的
    "symbol_direction"）。调用方不需要、也不应该自己拼接 key —— 一律
    通过 upsert_position() / remove_position() 操作，key 由 Position
    自己算出来，避免拼错顺序或者用了旧格式导致同一个持仓在字典里出现
    两条记录。
    """

    account_id: str                              # 账户唯一标识
    balance: float = 0.0                         # 账户总权益 (静态权益 + 浮动盈亏)
    available: float = 0.0                       # 可用资金
    frozen: float = 0.0                          # 挂单/保证金冻结资金
    positions: Dict[str, Position] = field(default_factory=dict)  # key: Position.contract_key

    @property
    def total_pnl(self) -> float:
        """计算当前组合的总浮动盈亏"""
        return sum(pos.pnl for pos in self.positions.values())

    @property
    def total_realized_pnl(self) -> float:
        """计算当前组合的总已实现盈亏"""
        return sum(pos.realized_pnl for pos in self.positions.values())

    def get_position(self, key: str) -> Optional[Position]:
        """按 contract_key 获取持仓对象；不存在返回 None"""
        return self.positions.get(key)

    def upsert_position(self, position: Position) -> None:
        """
        新增或更新一个持仓。

        key 由 position.contract_key 自动生成 —— 这是往 positions
        写数据的唯一推荐入口，不要直接操作 self.positions[...] = ...。
        """
        self.positions[position.contract_key] = position

    def remove_position(self, position_or_key: Union[Position, str]) -> None:
        """
        移除一个持仓。

        既可以传 Position 对象（会自动取它的 contract_key），
        也可以直接传 key 字符串。
        """
        key = (
            position_or_key.contract_key
            if isinstance(position_or_key, Position)
            else position_or_key
        )
        self.positions.pop(key, None)

    def positions_for_symbol(self, symbol: str) -> List[Position]:
        """
        获取某个标的下的全部持仓。

        期权场景下一个 symbol 可能同时存在多个方向 / 多个到期日 /
        行权价的持仓，所以这里返回的是列表而不是单个 Position。
        """
        return [
            position
            for position in self.positions.values()
            if position.symbol == symbol
        ]
