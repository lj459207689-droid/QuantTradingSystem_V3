# src/quant_system/core/interfaces/risk.py

from abc import ABC, abstractmethod
from typing import Tuple, Dict
from quant_system.core.entities import Order, Account, Position


class BaseRiskEngine(ABC):
    """
    风控引擎抽象接口 [cite: 10]
    包含事前订单风控校验与事中账户/组合风控监控 [cite: 10]
    """

    @abstractmethod
    def check_order_risk(
        self, 
        order: Order, 
        account: Account, 
        positions: Dict[str, Position]
    ) -> Tuple[bool, str]:
        """
        事前风控检查：在订单送达 IBKR 网关之前拦截 
        :return: (Is_Passed, Reason_If_Rejected) [cite: 11]
        校验项：购买力上限、单笔最大股数、防自相撮合、下订单频率限制等 [cite: 11]
        """
        pass

    @abstractmethod
    def check_portfolio_risk(
        self, 
        account: Account, 
        positions: Dict[str, Position]
    ) -> bool:
        """
        事中风控监控：每秒对账户总权益、最大回撤、单标的集中度进行检查 [cite: 11]
        触发风控报警或强平触发时返回 False [cite: 11]
        """
        pass