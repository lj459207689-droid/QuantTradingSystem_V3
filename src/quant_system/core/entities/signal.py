from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class Signal:
    """
    交易信号实体。

    用于表示策略或模型产生的交易信号。
    """

    symbol: str
    signal: str
    timestamp: datetime
    strength: float = 0.0
    price: float | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}