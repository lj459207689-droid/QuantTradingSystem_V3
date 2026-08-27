from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from quant_system.core.entities import Account, Order, Position


class BaseGateway(ABC):
    """
    交易所/券商网关抽象基类
    负责美股实时数据订阅 (1s Bar / Tick) 与订单生命周期管理 (IBKR)
    """

    def __init__(self, gateway_name: str):
        self.gateway_name: str = gateway_name

    @abstractmethod
    def connect(self, config: Dict[str, Any]) -> bool:
        """连接到券商交易端 (如 IB Gateway / TWS API)"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """断开券商连接"""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """检查网关当前连接状态"""
        pass

    # --- 行情流订阅 (Push/Callback 模式) ---
    @abstractmethod
    def subscribe(self, symbol: str) -> bool:
        """订阅指定美股标的之 1s Bar 与 Tick 实时数据流"""
        pass

    @abstractmethod
    def unsubscribe(self, symbol: str) -> bool:
        """取消订阅指定美股标的"""
        pass

    # --- 订单与交易执行 ---
    @abstractmethod
    def send_order(self, order: Order) -> str:
        """发送订单至券商，返回系统内部或券商分配的 order_id"""
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """根据订单 ID 撤销未成交委托"""
        pass

    # --- 资金与持仓同步 ---
    @abstractmethod
    def query_account(self) -> Optional[Account]:
        """主动查询当前账户资金、购买力及保证金状态"""
        pass

    @abstractmethod
    def query_positions(self) -> Dict[str, Position]:
        """主动查询当前全量持仓明细"""
        pass
