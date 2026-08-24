"""
Factor manager.

负责因子的注册、创建、计算和查询。
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .base import BaseFactor
from .registry import FactorRegistry


class FactorManager:
    """
    因子管理器。

    职责：

    1. 管理 FactorRegistry
    2. 注册因子
    3. 创建因子实例
    4. 计算单个因子
    5. 批量计算多个因子
    6. 查询因子
    7. 查询因子类别

    Manager 是 Factors 模块对外的主要入口。
    """

    def __init__(
        self,
        registry: FactorRegistry | None = None,
    ) -> None:

        self.registry = registry or FactorRegistry()

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        factor_class: type[BaseFactor],
    ) -> None:
        """
        注册一个因子类。
        """

        self.registry.register(
            factor_class
        )

    def unregister(
        self,
        name: str,
    ) -> None:
        """
        删除一个已经注册的因子。
        """

        self.registry.unregister(name)

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    def create(
        self,
        name: str,
        **kwargs: Any,
    ) -> BaseFactor:
        """
        根据名称创建因子实例。

        Example
        -------
        factor = manager.create(
            "sma",
            period=20,
        )
        """

        return self.registry.create(
            name,
            **kwargs,
        )

    # ------------------------------------------------------------------
    # Single factor calculation
    # ------------------------------------------------------------------

    def calculate(
        self,
        name: str,
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> pd.Series:
        """
        计算单个因子。

        Parameters
        ----------
        name:
            因子名称。

        data:
            市场历史数据。

        kwargs:
            因子参数。

        Returns
        -------
        pandas.Series
            因子结果。
        """

        factor = self.create(
            name,
            **kwargs,
        )

        return factor.calculate(data)

    # ------------------------------------------------------------------
    # Batch calculation
    # ------------------------------------------------------------------

    def calculate_many(
        self,
        data: pd.DataFrame,
        factors: (
            list[str]
            | dict[str, dict[str, Any]]
        ),
    ) -> pd.DataFrame:
        """
        批量计算多个因子。

        支持：

        方式一：

            [
                "sma",
                "ema",
                "momentum",
            ]

        方式二：

            {
                "sma": {
                    "period": 20,
                },
                "ema": {
                    "period": 20,
                },
            }
        """

        if not isinstance(
            data,
            pd.DataFrame,
        ):
            raise TypeError(
                "data must be a pandas DataFrame"
            )

        if isinstance(factors, list):

            factor_configs = {
                name: {}
                for name in factors
            }

        elif isinstance(factors, dict):

            factor_configs = factors

        else:

            raise TypeError(
                "factors must be a list or dict"
            )

        results: dict[str, pd.Series] = {}

        for name, kwargs in factor_configs.items():

            if kwargs is None:
                kwargs = {}

            if not isinstance(kwargs, dict):
                raise TypeError(
                    f"Parameters for factor "
                    f"'{name}' must be a dict"
                )

            result = self.calculate(
                name,
                data,
                **kwargs,
            )

            results[name] = result

        if not results:

            return pd.DataFrame(
                index=data.index
            )

        return pd.DataFrame(
            results,
            index=data.index,
        )

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def exists(
        self,
        name: str,
    ) -> bool:
        """
        判断因子是否存在。
        """

        return self.registry.exists(name)

    def list_factors(self) -> list[str]:
        """
        返回所有已经注册的因子。
        """

        return self.registry.names()

    def list_categories(
        self,
    ) -> dict[str, list[str]]:
        """
        返回按照类别组织的因子。
        """

        return self.registry.categories()

    # ------------------------------------------------------------------
    # Registry access
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """
        清空所有已注册因子。
        """

        self.registry.clear()

    def __len__(self) -> int:
        return len(self.registry)

    def __contains__(
        self,
        name: str,
    ) -> bool:
        return name in self.registry

    def __repr__(self) -> str:
        return (
            f"FactorManager("
            f"count={len(self)}, "
            f"factors={self.list_factors()}"
            f")"
        )