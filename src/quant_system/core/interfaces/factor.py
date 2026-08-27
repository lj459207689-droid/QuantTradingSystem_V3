"""
Factor interface.

定义量化交易系统中所有因子的统一接口。

设计目标：
1. 支持流式数据逐条更新
2. 支持滑动窗口
3. 支持获取最新因子值
4. 支持重置内部状态
5. 不依赖具体 Factor 实现
6. 不依赖 DataManager / Strategy / Broker
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

import pandas as pd


class Factor(ABC):
    """
    因子统一抽象接口。

    所有具体因子都必须继承 Factor。

    生命周期：

        market data
             ↓
        update(data)
             ↓
        internal state
             ↓
           value

    例如：

        SMA.update(bar)
        SMA.value

    """

    # ------------------------------------------------------------------
    # 元数据
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def name(self) -> str:
        """
        因子唯一名称。

        例如：

            "sma"
            "momentum"
            "realized_volatility"
            "ofi"
        """
        raise NotImplementedError

    @property
    def category(self) -> str:
        """
        因子所属类别。

        默认类别为 "unknown"。

        子类可以覆盖：

            trend
            momentum
            volatility
            volume
            microstructure
            fundamental
            options
        """
        return "unknown"

    @property
    def description(self) -> str:
        """
        因子描述。
        """
        return ""

    # ------------------------------------------------------------------
    # 数据更新
    # ------------------------------------------------------------------

    @abstractmethod
    def update(
        self,
        data: Any,
    ) -> Optional[float]:
        """
        使用最新市场数据更新因子。

        Parameters
        ----------
        data:
            最新市场数据。

            可以是：
            - Bar
            - Tick
            - dict
            - pandas.Series
            - 其他标准化市场数据对象

        Returns
        -------
        Optional[float]
            更新后的最新因子值。

            如果当前数据不足以计算因子，
            可以返回 None。

        Notes
        -----
        update() 是实时/流式因子的核心接口。

        例如：

            factor.update(bar)
            value = factor.value
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # 批量计算
    # ------------------------------------------------------------------

    def calculate(
        self,
        data: pd.DataFrame,
    ) -> pd.Series:
        """
        对历史 DataFrame 进行批量计算。

        默认实现通过 update() 逐行计算。

        子类可以覆盖该方法，以实现更高性能的
        向量化计算。

        Parameters
        ----------
        data:
            历史市场数据。

        Returns
        -------
        pandas.Series
            与输入 DataFrame index 对齐的因子序列。

        Notes
        -----
        默认实现强调接口统一，而不是极致性能。

        后续可以针对 SMA、EMA、ATR、OFI 等因子
        分别实现向量化版本。
        """

        if not isinstance(data, pd.DataFrame):
            raise TypeError(
                "data must be a pandas DataFrame"
            )

        if data.empty:
            return pd.Series(
                index=data.index,
                dtype=float,
                name=self.name,
            )

        # 批量计算前先清除旧状态，
        # 防止历史状态污染新的计算任务。
        self.reset()

        values: list[Optional[float]] = []

        for _, row in data.iterrows():
            values.append(self.update(row))

        return pd.Series(
            values,
            index=data.index,
            dtype=float,
            name=self.name,
        )

    # ------------------------------------------------------------------
    # 当前值
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def value(self) -> Optional[float]:
        """
        获取当前最新的因子计算结果。

        Returns
        -------
        Optional[float]
            当前因子值。

            如果尚未达到计算所需的数据长度，
            返回 None。
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # 状态
    # ------------------------------------------------------------------

    @abstractmethod
    def reset(self) -> None:
        """
        重置内部状态。

        应清除：

        - 滑动窗口
        - 累计值
        - 当前因子值
        - 中间计算状态
        - 其他缓存

        重置后：

            factor.value is None

        或由具体因子定义适当的初始状态。
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # 就绪状态
    # ------------------------------------------------------------------

    @property
    def is_ready(self) -> bool:
        """
        判断因子当前是否已经具备有效计算结果。

        默认通过 value 判断。

        子类可以覆盖该属性实现更精确的判断。
        """
        return self.value is not None

    # ------------------------------------------------------------------
    # 元数据
    # ------------------------------------------------------------------

    @property
    def metadata(self) -> dict[str, Any]:
        """
        返回因子元数据。

        用于：

        - FactorManager
        - FactorRegistry
        - FactorEvaluator
        - FactorSelector
        - 日志
        - 研究报告
        """

        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
        }

    # ------------------------------------------------------------------
    # 调用接口
    # ------------------------------------------------------------------

    def __call__(
        self,
        data: Any,
    ) -> Optional[float]:
        """
        允许：

            factor(data)

        等价于：

            factor.update(data)
        """
        return self.update(data)

    # ------------------------------------------------------------------
    # 字符串表示
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"category='{self.category}'"
            f")"
        )
