# src/quant_system/core/interfaces/strategy.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from quant_system.core.entities import Bar, Order, Tick, Trade


class BaseStrategy(ABC):
    """
    量化交易策略抽象基类 [cite: 13]
    定义美股 1 秒级策略的生命周期管理与事件驱动响应接口 [cite: 13, 14]
    """

    def __init__(self, strategy_id: str, symbols: List[str], config: Dict[str, Any]):
        self.strategy_id: str = strategy_id
        self.symbols: List[str] = symbols
        self.config: Dict[str, Any] = config
        self.is_active: bool = False

    # --- 策略生命周期管理 ---
    @abstractmethod
    def on_init(self) -> None:
        """策略初始化回调：加载因子、加载 AI 模型权重、历史数据预热 [cite: 14]"""
        pass

    @abstractmethod
    def on_start(self) -> None:
        """策略启动回调：开启事件监听与实盘/模拟推送 [cite: 14]"""
        pass

    @abstractmethod
    def on_stop(self) -> None:
        """策略停止回调：平仓、撤单、保存策略状态与日志 [cite: 14, 15]"""
        pass

    # --- 行情与交易事件回调 ---
    @abstractmethod
    def on_bar(self, bar: Bar) -> None:
        """1 秒 K 线数据推送回调 (策略主驱动核心) [cite: 15]"""
        pass

    @abstractmethod
    def on_tick(self, tick: Tick) -> None:
        """Tick 实时深度盘口回调 [cite: 15]"""
        pass

    @abstractmethod
    def on_order(self, order: Order) -> None:
        """委托单状态变更回调 (如已提交、部分成交、已撤销、被拒绝) [cite: 15]"""
        pass

    @abstractmethod
    def on_trade(self, trade: Trade) -> None:
        """最新成交回报回调 [cite: 16]"""
        pass
