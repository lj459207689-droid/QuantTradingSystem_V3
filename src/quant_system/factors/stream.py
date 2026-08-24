"""
Factor streaming engine.

负责将实时市场数据持续发送给 FactorPipeline，
实现因子的流式计算。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional

from .pipeline import FactorPipeline


@dataclass
class FactorStreamResult:
    """
    单次流式计算结果。

    Parameters
    ----------
    timestamp:
        当前数据时间。

    values:
        当前所有因子的值。

    ready:
        Pipeline 是否已经全部准备完成。
    """

    timestamp: Optional[datetime]
    values: dict[str, Any]
    ready: bool

    def get(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        获取指定因子值。
        """

        return self.values.get(
            name,
            default,
        )

    def __getitem__(
        self,
        name: str,
    ) -> Any:
        return self.values[name]

    def __contains__(
        self,
        name: str,
    ) -> bool:
        return name in self.values


class FactorStream:
    """
    因子流式计算引擎。

    职责：

    1. 接收实时市场数据
    2. 调用 FactorPipeline.update()
    3. 保存最新因子值
    4. 提供回调机制
    5. 支持 reset
    6. 统计处理数量

    典型流程：

        IBKRRealtimeDataProvider
                ↓
             Bar/Tick
                ↓
          FactorStream.update()
                ↓
          FactorPipeline
                ↓
          Factor values
                ↓
             Strategy
    """

    def __init__(
        self,
        pipeline: FactorPipeline,
        callback: (
            Callable[[FactorStreamResult], None]
            | None
        ) = None,
    ) -> None:

        if not isinstance(
            pipeline,
            FactorPipeline,
        ):
            raise TypeError(
                "pipeline must be a FactorPipeline"
            )

        self.pipeline = pipeline
        self.callback = callback

        self._count: int = 0
        self._last_result: Optional[
            FactorStreamResult
        ] = None

        self._running: bool = False

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def count(self) -> int:
        """
        已处理的数据数量。
        """

        return self._count

    @property
    def running(self) -> bool:
        """
        当前是否处于运行状态。
        """

        return self._running

    @property
    def last_result(
        self,
    ) -> Optional[FactorStreamResult]:
        """
        获取最近一次计算结果。
        """

        return self._last_result

    @property
    def values(self) -> dict[str, Any]:
        """
        获取最新因子值。
        """

        if self._last_result is None:
            return {}

        return dict(
            self._last_result.values
        )

    @property
    def is_ready(self) -> bool:
        """
        判断所有因子是否已经准备完成。
        """

        return self.pipeline.is_ready

    # ------------------------------------------------------------------
    # Streaming
    # ------------------------------------------------------------------

    def update(
        self,
        data: Any,
        timestamp: Optional[datetime] = None,
    ) -> FactorStreamResult:
        """
        输入一条实时市场数据。

        Parameters
        ----------
        data:
            Bar / Tick / 标准化市场数据。

        timestamp:
            数据时间。

        Returns
        -------
        FactorStreamResult
            当前因子计算结果。
        """

        values = self.pipeline.update(
            data
        )

        self._count += 1

        result = FactorStreamResult(
            timestamp=timestamp,
            values=dict(values),
            ready=self.pipeline.is_ready,
        )

        self._last_result = result

        if self.callback is not None:
            self.callback(result)

        return result

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """
        启动流式计算状态。

        注意：
        start() 不负责连接 IBKR。
        数据源连接由 DataManager / RealtimeDataProvider
        管理。
        """

        self._running = True

    def stop(self) -> None:
        """
        停止流式计算。

        不清除因子状态。
        """

        self._running = False

    def reset(self) -> None:
        """
        重置整个流式计算状态。

        包括：

        - Pipeline
        - 所有 Factor
        - 数据计数
        - 最近结果
        """

        self.pipeline.reset()

        self._count = 0
        self._last_result = None

    # ------------------------------------------------------------------
    # Callback
    # ------------------------------------------------------------------

    def set_callback(
        self,
        callback: (
            Callable[[FactorStreamResult], None]
            | None
        ),
    ) -> None:
        """
        设置结果回调函数。

        Example
        -------

            def on_factor(result):
                print(result.values)

            stream.set_callback(on_factor)
        """

        if callback is not None and not callable(
            callback
        ):
            raise TypeError(
                "callback must be callable or None"
            )

        self.callback = callback

    # ------------------------------------------------------------------
    # Batch streaming
    # ------------------------------------------------------------------

    def update_many(
        self,
        data_iterable,
    ) -> list[FactorStreamResult]:
        """
        连续处理多条数据。

        Parameters
        ----------
        data_iterable:
            任意可迭代数据源。

        Returns
        -------
        list[FactorStreamResult]
            每条数据对应的计算结果。
        """

        results: list[FactorStreamResult] = []

        for data in data_iterable:
            results.append(
                self.update(data)
            )

        return results

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"FactorStream("
            f"count={self.count}, "
            f"running={self.running}, "
            f"ready={self.is_ready}, "
            f"factors={self.pipeline.names()}"
            f")"
        )