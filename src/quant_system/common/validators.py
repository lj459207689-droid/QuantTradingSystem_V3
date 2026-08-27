"""
QuantTradingSystem V3
Common Validators

通用参数和数据验证。

注意：
    本模块只做通用验证。
    不处理 Order、Position、Strategy 等业务对象。
"""

from __future__ import annotations

import math
from datetime import date, datetime
from typing import Any

from .exceptions import ValidationError


def validate_not_none(
    value: Any,
    name: str = "value",
) -> Any:
    """验证值不能为 None。"""
    if value is None:
        raise ValidationError(f"{name} cannot be None.")

    return value


def validate_not_empty(
    value: str,
    name: str = "value",
) -> str:
    """验证字符串不能为空。"""
    if not isinstance(value, str):
        raise ValidationError(
            f"{name} must be a string."
        )

    if not value.strip():
        raise ValidationError(
            f"{name} cannot be empty."
        )

    return value


def validate_positive(
    value: float | int,
    name: str = "value",
) -> float | int:
    """验证数值必须大于 0。"""
    if not isinstance(value, (int, float)):
        raise ValidationError(
            f"{name} must be numeric."
        )

    if isinstance(value, bool):
        raise ValidationError(
            f"{name} must be numeric."
        )

    if not math.isfinite(float(value)):
        raise ValidationError(
            f"{name} must be finite."
        )

    if value <= 0:
        raise ValidationError(
            f"{name} must be greater than zero."
        )

    return value


def validate_non_negative(
    value: float | int,
    name: str = "value",
) -> float | int:
    """验证数值必须大于或等于 0。"""
    if not isinstance(value, (int, float)):
        raise ValidationError(
            f"{name} must be numeric."
        )

    if isinstance(value, bool):
        raise ValidationError(
            f"{name} must be numeric."
        )

    if not math.isfinite(float(value)):
        raise ValidationError(
            f"{name} must be finite."
        )

    if value < 0:
        raise ValidationError(
            f"{name} cannot be negative."
        )

    return value


def validate_percentage(
    value: float | int,
    name: str = "value",
) -> float | int:
    """
    验证百分比数值在 0~1 范围。

    例如：
        0.05 = 5%
        0.20 = 20%
    """
    validate_non_negative(value, name)

    if value > 1:
        raise ValidationError(
            f"{name} must be between 0 and 1."
        )

    return value


def validate_range(
    value: float | int,
    minimum: float | int,
    maximum: float | int,
    name: str = "value",
) -> float | int:
    """验证数值范围。"""
    if minimum > maximum:
        raise ValidationError(
            "minimum cannot be greater than maximum."
        )

    if value < minimum or value > maximum:
        raise ValidationError(
            f"{name} must be between "
            f"{minimum} and {maximum}."
        )

    return value


def validate_date_range(
    start: date | datetime,
    end: date | datetime,
) -> tuple[date | datetime, date | datetime]:
    """验证日期范围。"""
    if end < start:
        raise ValidationError(
            "End date cannot be earlier than start date."
        )

    return start, end


def validate_instance(
    value: Any,
    expected_type: type,
    name: str = "value",
) -> Any:
    """验证对象类型。"""
    if not isinstance(value, expected_type):
        raise ValidationError(
            f"{name} must be "
            f"{expected_type.__name__}."
        )

    return value
