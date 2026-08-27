"""
QuantTradingSystem V3
Common Utilities

非常通用的小型工具函数。

原则：
    不放交易策略、技术指标、风险模型、
    订单执行等业务逻辑。
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    """将数值限制在指定范围内。"""
    if minimum > maximum:
        raise ValueError(
            "minimum cannot be greater than maximum."
        )

    return max(minimum, min(value, maximum))


def chunks(
    items: list[T],
    size: int,
) -> list[list[T]]:
    """
    将列表拆分成固定大小的块。

    Example
    -------
    chunks([1, 2, 3, 4, 5], 2)
    -> [[1, 2], [3, 4], [5]]
    """
    if size <= 0:
        raise ValueError("size must be greater than zero.")

    return [
        items[index:index + size]
        for index in range(0, len(items), size)
    ]


def flatten(
    items: Iterable[Iterable[T]],
) -> list[T]:
    """展开二维 iterable。"""
    return [
        item
        for group in items
        for item in group
    ]


def first_not_none(
    *values: T | None,
) -> T | None:
    """返回第一个非 None 值。"""
    for value in values:
        if value is not None:
            return value

    return None


def safe_float(
    value: object,
    default: float | None = None,
) -> float | None:
    """安全转换为 float。"""
    try:
        if value is None:
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def safe_int(
    value: object,
    default: int | None = None,
) -> int | None:
    """安全转换为 int。"""
    try:
        if value is None:
            return default

        return int(value)

    except (TypeError, ValueError):
        return default
