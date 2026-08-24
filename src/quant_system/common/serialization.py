"""
QuantTradingSystem V3
Common Serialization

通用对象序列化工具。

架构规则：
    本模块禁止依赖 quant_system.core。

    Common 只负责：
        Python object
            ↓
        primitive data
            ↓
        JSON

    不负责识别：
        Bar
        Tick
        Order
        Fill
        Position
        Portfolio
        Signal
        Trade
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .exceptions import SerializationError


Primitive = str | int | float | bool | None


def serialize(obj: Any) -> Any:
    """
    将对象转换为 JSON-compatible Python object。

    不依赖任何 quant_system 业务模块。
    """

    if obj is None:
        return None

    if isinstance(obj, (str, int, float, bool)):
        return obj

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    if isinstance(obj, Enum):
        return serialize(obj.value)

    if is_dataclass(obj) and not isinstance(obj, type):
        return serialize(asdict(obj))

    if isinstance(obj, dict):
        return {
            str(key): serialize(value)
            for key, value in obj.items()
        }

    if isinstance(obj, (list, tuple, set, frozenset)):
        return [serialize(item) for item in obj]

    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        return serialize(obj.to_dict())

    raise SerializationError(
        f"Unsupported object type: {type(obj).__name__}"
    )


def to_json(
    obj: Any,
    *,
    indent: int | None = None,
    ensure_ascii: bool = False,
) -> str:
    """将对象序列化为 JSON 字符串。"""
    try:
        return json.dumps(
            serialize(obj),
            indent=indent,
            ensure_ascii=ensure_ascii,
        )
    except (TypeError, ValueError) as exc:
        raise SerializationError(
            f"Failed to serialize object: {exc}"
        ) from exc


def from_json(value: str) -> Any:
    """从 JSON 字符串读取 Python 对象。"""
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise SerializationError(
            f"Invalid JSON: {exc}"
        ) from exc


def dump_json(
    obj: Any,
    path: str | Path,
    *,
    indent: int = 2,
    ensure_ascii: bool = False,
) -> None:
    """将对象序列化并保存到 JSON 文件。"""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        file_path.write_text(
            to_json(
                obj,
                indent=indent,
                ensure_ascii=ensure_ascii,
            ),
            encoding="utf-8",
        )
    except OSError as exc:
        raise SerializationError(
            f"Failed to write JSON file: {file_path}"
        ) from exc


def load_json(path: str | Path) -> Any:
    """从 JSON 文件读取对象。"""
    file_path = Path(path)

    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SerializationError(
            f"Failed to read JSON file: {file_path}"
        ) from exc

    return from_json(content)