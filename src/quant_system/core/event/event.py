from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """系统事件类型定义"""
    # 行情事件
    TICK = "eTick"             # 实时 Tick 数据到达
    BAR_1S = "eBar1s"          # 1秒 K线数据到达
    
    # 交易与信号事件
    SIGNAL = "eSignal"         # 策略生成交易信号
    ORDER = "eOrder"           # 订单状态变动
    FILL = "eFill"             # 成交回报
    
    # 系统与定时器事件
    TIMER = "eTimer"           # 定时器驱动
    LOG = "eLog"               # 系统日志事件
    ERROR = "eError"           # 系统异常


@dataclass
class Event:
    """标准事件容器"""
    type: EventType            # 事件类型
    data: Any = None           # 载荷数据
    timestamp: datetime = field(default_factory=datetime.now)
