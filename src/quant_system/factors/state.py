"""
Factor state utilities.

提供因子计算过程中通用的状态和滑动窗口基础设施。
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Iterable, Iterator, Optional


class RollingWindow:
    """
    固定长度滑动窗口。

    用于保存因子最近 N 个数据。

    Example
    -------
    window = RollingWindow(3)

    window.append(1)
    window.append(2)
    window.append(3)
    window.append(4)

    结果：

        [2, 3, 4]
    """

    def __init__(self, size: int) -> None:
        if not isinstance(size, int):
            raise TypeError("size must be an integer")

        if size <= 0:
            raise ValueError("size must be greater than zero")

        self._size = size
        self._data: Deque[float] = deque(maxlen=size)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        """窗口最大长度。"""
        return self._size

    @property
    def count(self) -> int:
        """当前窗口中的数据数量。"""
        return len(self._data)

    @property
    def is_full(self) -> bool:
        """判断窗口是否已经填满。"""
        return len(self._data) >= self._size

    @property
    def latest(self) -> Optional[float]:
        """获取窗口最新值。"""
        if not self._data:
            return None

        return self._data[-1]

    @property
    def oldest(self) -> Optional[float]:
        """获取窗口最旧值。"""
        if not self._data:
            return None

        return self._data[0]

    # ------------------------------------------------------------------
    # Data operations
    # ------------------------------------------------------------------

    def append(self, value: float) -> None:
        """
        添加一个数据。

        如果窗口已满，则自动删除最旧数据。
        """

        self._data.append(float(value))

    def extend(
        self,
        values: Iterable[float],
    ) -> None:
        """批量添加数据。"""

        for value in values:
            self.append(value)

    def clear(self) -> None:
        """清空窗口。"""
        self._data.clear()

    def values(self) -> list[float]:
        """返回窗口数据副本。"""
        return list(self._data)

    def sum(self) -> float:
        """计算窗口数据总和。"""
        return sum(self._data)

    def mean(self) -> Optional[float]:
        """
        计算窗口平均值。

        空窗口返回 None。
        """

        if not self._data:
            return None

        return sum(self._data) / len(self._data)

    def min(self) -> Optional[float]:
        """返回窗口最小值。"""

        if not self._data:
            return None

        return min(self._data)

    def max(self) -> Optional[float]:
        """返回窗口最大值。"""

        if not self._data:
            return None

        return max(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator[float]:
        return iter(self._data)

    def __getitem__(self, index: int) -> float:
        return list(self._data)[index]

    def __repr__(self) -> str:
        return (
            f"RollingWindow("
            f"size={self.size}, "
            f"count={self.count}, "
            f"values={self.values()}"
            f")"
        )


@dataclass
class FactorState:
    """
    通用因子状态。

    用于保存因子计算过程中需要持续维护的信息。

    Parameters
    ----------
    window_size:
        滑动窗口长度。
    """

    window_size: Optional[int] = None

    window: Optional[RollingWindow] = field(
        default=None,
        init=False,
    )

    count: int = field(
        default=0,
        init=False,
    )

    last_value: Optional[float] = field(
        default=None,
        init=False,
    )

    cumulative_value: float = field(
        default=0.0,
        init=False,
    )

    def __post_init__(self) -> None:
        if self.window_size is not None:

            if not isinstance(
                self.window_size,
                int,
            ):
                raise TypeError(
                    "window_size must be an integer or None"
                )

            if self.window_size <= 0:
                raise ValueError(
                    "window_size must be greater than zero"
                )

            self.window = RollingWindow(
                self.window_size
            )

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(
        self,
        value: float,
    ) -> None:
        """
        更新状态。
        """

        value = float(value)

        self.count += 1
        self.last_value = value
        self.cumulative_value += value

        if self.window is not None:
            self.window.append(value)

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """
        重置全部状态。
        """

        self.count = 0
        self.last_value = None
        self.cumulative_value = 0.0

        if self.window is not None:
            self.window.clear()

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @property
    def is_ready(self) -> bool:
        """
        判断状态是否已经达到计算条件。

        如果配置了 window_size，
        则要求窗口填满。

        如果没有窗口，
        则至少需要一个数据。
        """

        if self.window is not None:
            return self.window.is_full

        return self.count > 0

    def __repr__(self) -> str:
        return (
            f"FactorState("
            f"count={self.count}, "
            f"last_value={self.last_value}, "
            f"cumulative_value={self.cumulative_value}, "
            f"window={self.window}"
            f")"
        )