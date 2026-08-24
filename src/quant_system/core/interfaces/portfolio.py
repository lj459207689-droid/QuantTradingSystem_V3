"""
Portfolio Interface
===================

定义量化交易系统中 Portfolio（投资组合）的标准接口。

设计原则：
1. 接口与实现分离
2. Portfolio 负责组合状态访问
3. PortfolioManager 负责具体业务逻辑
4. 不依赖具体 Broker、数据库或策略实现
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any


class IPortfolio(ABC):
    """
    Portfolio 组合管理接口。

    所有具体 Portfolio 实现都必须实现本接口定义的方法。
    """

    # ============================================================
    # Position
    # ============================================================

    @abstractmethod
    def get_position(self, symbol: str) -> Optional[Any]:
        """
        获取指定标的的持仓。

        Parameters
        ----------
        symbol : str
            标的代码，例如 NVDA、TSLA。

        Returns
        -------
        Optional[Any]
            Position 对象；如果没有持仓则返回 None。
        """
        pass

    @abstractmethod
    def get_positions(self) -> Dict[str, Any]:
        """
        获取全部持仓。

        Returns
        -------
        Dict[str, Any]
            {symbol: Position}
        """
        pass

    @abstractmethod
    def update_position(self, symbol: str, position: Any) -> None:
        """
        更新指定标的的持仓。

        Parameters
        ----------
        symbol : str
            标的代码。

        position : Any
            Position 对象。
        """
        pass

    # ============================================================
    # Cash
    # ============================================================

    @abstractmethod
    def get_cash(self) -> float:
        """
        获取当前现金余额。

        Returns
        -------
        float
            Cash balance。
        """
        pass

    # ============================================================
    # Portfolio Value
    # ============================================================

    @abstractmethod
    def get_market_value(self) -> float:
        """
        获取当前持仓市值。

        Returns
        -------
        float
            Market value。
        """
        pass

    @abstractmethod
    def get_equity(self) -> float:
        """
        获取组合总权益。

        Equity = Cash + Market Value
        """
        pass

    @abstractmethod
    def calculate_portfolio_value(self) -> float:
        """
        计算当前 Portfolio 总价值。

        Returns
        -------
        float
            Portfolio value。
        """
        pass

    # ============================================================
    # PnL
    # ============================================================

    @abstractmethod
    def get_realized_pnl(self) -> float:
        """
        获取已实现盈亏。
        """
        pass

    @abstractmethod
    def get_unrealized_pnl(self) -> float:
        """
        获取未实现盈亏。
        """
        pass

    @abstractmethod
    def get_total_pnl(self) -> float:
        """
        获取总盈亏。

        Total PnL =
            Realized PnL + Unrealized PnL
        """
        pass

    # ============================================================
    # Exposure
    # ============================================================

    @abstractmethod
    def get_exposure(self, symbol: Optional[str] = None) -> float:
        """
        获取组合风险敞口。

        Parameters
        ----------
        symbol : Optional[str]
            如果指定，则返回单一标的敞口；
            如果为 None，则返回整个组合敞口。

        Returns
        -------
        float
            Exposure。
        """
        pass

    @abstractmethod
    def get_exposures(self) -> Dict[str, float]:
        """
        获取所有标的的风险敞口。

        Returns
        -------
        Dict[str, float]
            {symbol: exposure}
        """
        pass

    # ============================================================
    # Portfolio Snapshot
    # ============================================================

    @abstractmethod
    def get_snapshot(self) -> Dict[str, Any]:
        """
        获取当前组合状态快照。

        Returns
        -------
        Dict[str, Any]
            Portfolio snapshot。
        """
        pass

    # ============================================================
    # Reset
    # ============================================================

    @abstractmethod
    def reset(self) -> None:
        """
        重置 Portfolio。
        """
        pass