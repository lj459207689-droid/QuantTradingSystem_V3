"""
Base factor implementation.

提供所有具体因子共享的基础功能。
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Optional

import pandas as pd

from quant_system.core.interfaces.factor import Factor


class BaseFactor(Factor):
    """
    所有具体因子的基础类。

    职责：
    - 提供因子元数据
    - 提供批量计算能力
    - 提供输入验证
    - 保持统一的 Factor 接口
    """

    category: str = "unknown"
    description: str = ""

    def __init__(self) -> None:
        self._value: Optional[float] = None

    @property
    @abstractmethod
    def name(self) -> str:
        """因子唯一名称。"""
        raise NotImplementedError

    @property
    def category(self) -> str:
        """因子类别。"""
        return self.__class__.category

    @property
    def description(self) -> str:
        """因子描述。"""
        return self.__class__.description

    @property
    def value(self) -> Optional[float]:
        """当前最新因子值。"""
        return self._value

    def validate_input(self, data: Any) -> None:
        """
        验证输入数据。

        子类可以覆盖此方法增加专用检查。
        """
        if data is None:
            raise ValueError("Factor input data cannot be None")

    def calculate(
        self,
        data: pd.DataFrame,
    ) -> pd.Series:
        """
        对历史数据进行批量计算。

        默认通过 update() 逐行计算。
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

        self.reset()

        values: list[Optional[float]] = []

        for _, row in data.iterrows():
            values.append(
                self.update(row)
            )

        return pd.Series(
            values,
            index=data.index,
            dtype=float,
            name=self.name,
        )

    @property
    def is_ready(self) -> bool:
        """
        判断因子是否已经产生有效结果。
        """
        return self.value is not None

    @property
    def metadata(self) -> dict[str, Any]:
        """
        获取因子元数据。
        """
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
        }

    def __call__(
        self,
        data: Any,
    ) -> Optional[float]:
        """
        factor(data)

        等价于：

        factor.update(data)
        """
        return self.update(data)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"category='{self.category}'"
            f")"
        )