# src/quant_system/core/interfaces/execution.py

from abc import ABC, abstractmethod
from typing import List

from quant_system.core.entities import Bar, Order, Signal


class BaseExecutionEngine(ABC):
    """
    智能算法执行引擎抽象接口 [cite: 12]
    实现 TWAP, VWAP, Sniper 等微观拆单与挂单追踪逻辑 [cite: 12, 13]
    """

    @abstractmethod
    def execute_signal(self, signal: Signal) -> List[Order]:
        """
        将策略高层 Trading Signal (如买入 5000 股 AAPL) 转换为初始拆单列表 [cite: 12]
        """
        pass

    @abstractmethod
    def on_1s_step(self, bar: Bar) -> List[Order]:
        """
        1秒驱动定时器：根据最新盘口微观结构更新未成交订单 (追单/改单/撤单) [cite: 13]
        """
        pass
