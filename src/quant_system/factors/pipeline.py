"""
Factor pipeline.

负责组织多个因子的统一计算流程。

Pipeline 不负责：
- 因子注册
- 因子选择
- 因子评价
- 交易信号生成

Pipeline 只负责：
- 管理一组 Factor
- 批量历史计算
- 流式更新
- 返回统一结果
"""

from __future__ import annotations

from typing import Any, Iterable

import pandas as pd

from quant_system.core.interfaces.factor import Factor


class FactorPipeline:
    """
    因子计算流水线。

    一个 Pipeline 可以包含多个 Factor。

    例如：

        SMA
        EMA
        Momentum
        ATR

    统一执行：

        pipeline.calculate(data)

    或实时执行：

        pipeline.update(bar)
    """

    def __init__(
        self,
        factors: Iterable[Factor] | None = None,
    ) -> None:

        self._factors: dict[str, Factor] = {}

        if factors is not None:
            for factor in factors:
                self.add(factor)

    # ------------------------------------------------------------------
    # Factor management
    # ------------------------------------------------------------------

    def add(
        self,
        factor: Factor,
    ) -> None:
        """
        添加一个因子。

        Parameters
        ----------
        factor:
            Factor 实例。
        """

        if not isinstance(factor, Factor):
            raise TypeError(
                "factor must be an instance of Factor"
            )

        name = factor.name

        if not name:
            raise ValueError(
                "Factor name cannot be empty"
            )

        if name in self._factors:
            raise ValueError(
                f"Factor already exists in pipeline: {name}"
            )

        self._factors[name] = factor

    def remove(
        self,
        name: str,
    ) -> None:
        """
        删除一个因子。
        """

        if name not in self._factors:
            raise KeyError(
                f"Factor not found in pipeline: {name}"
            )

        del self._factors[name]

    def get(
        self,
        name: str,
    ) -> Factor:
        """
        获取指定因子。
        """

        if name not in self._factors:
            raise KeyError(
                f"Factor not found in pipeline: {name}"
            )

        return self._factors[name]

    def has(
        self,
        name: str,
    ) -> bool:
        """
        判断 Pipeline 是否包含指定因子。
        """

        return name in self._factors

    def names(self) -> list[str]:
        """
        返回 Pipeline 中所有因子名称。
        """

        return list(self._factors.keys())

    def factors(self) -> list[Factor]:
        """
        返回所有因子实例。
        """

        return list(self._factors.values())

    # ------------------------------------------------------------------
    # Historical calculation
    # ------------------------------------------------------------------

    def calculate(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        使用历史数据批量计算所有因子。

        Parameters
        ----------
        data:
            市场历史数据。

        Returns
        -------
        pandas.DataFrame
            每个因子对应一列。
        """

        if not isinstance(
            data,
            pd.DataFrame,
        ):
            raise TypeError(
                "data must be a pandas DataFrame"
            )

        if not self._factors:
            return pd.DataFrame(
                index=data.index
            )

        results: dict[str, pd.Series] = {}

        for name, factor in self._factors.items():

            results[name] = factor.calculate(
                data
            )

        return pd.DataFrame(
            results,
            index=data.index,
        )

    # ------------------------------------------------------------------
    # Streaming calculation
    # ------------------------------------------------------------------

    def update(
        self,
        data: Any,
    ) -> dict[str, Any]:
        """
        使用最新市场数据更新所有因子。

        Parameters
        ----------
        data:
            最新 Bar / Tick / 标准化市场数据。

        Returns
        -------
        dict[str, Any]
            当前所有因子的最新值。
        """

        values: dict[str, Any] = {}

        for name, factor in self._factors.items():

            values[name] = factor.update(
                data
            )

        return values

    # ------------------------------------------------------------------
    # Current values
    # ------------------------------------------------------------------

    @property
    def values(self) -> dict[str, Any]:
        """
        获取所有因子的当前值。
        """

        return {
            name: factor.value
            for name, factor in self._factors.items()
        }

    # ------------------------------------------------------------------
    # Ready status
    # ------------------------------------------------------------------

    @property
    def is_ready(self) -> bool:
        """
        判断 Pipeline 中所有因子是否已经准备完成。

        空 Pipeline 返回 False。
        """

        if not self._factors:
            return False

        return all(
            factor.is_ready
            for factor in self._factors.values()
        )

    def ready_factors(self) -> list[str]:
        """
        返回已经产生有效值的因子。
        """

        return [
            name
            for name, factor in self._factors.items()
            if factor.is_ready
        ]

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """
        重置所有因子。
        """

        for factor in self._factors.values():
            factor.reset()

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    @property
    def metadata(self) -> dict[str, dict[str, Any]]:
        """
        返回所有因子的元数据。
        """

        return {
            name: factor.metadata
            for name, factor in self._factors.items()
        }

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._factors)

    def __contains__(
        self,
        name: str,
    ) -> bool:
        return self.has(name)

    def __iter__(self):
        return iter(self._factors.values())

    def __repr__(self) -> str:
        return (
            f"FactorPipeline("
            f"count={len(self)}, "
            f"factors={self.names()}"
            f")"
        )
