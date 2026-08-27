"""
QuantTradingSystem V3
Trading Calendar

通用交易日历基础设施。

注意：
    Common 层不依赖具体交易所业务模块。
    本模块提供通用的工作日、假日和交易时段判断能力。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Iterable

from .exceptions import CalendarError


@dataclass(frozen=True)
class TradingSession:
    """一个交易时段。"""

    name: str
    open_time: time
    close_time: time


@dataclass
class TradingCalendar:
    """
    通用交易日历。

    默认：
        周一至周五为交易日。
        holidays 中的日期视为非交易日。
    """

    name: str = "DEFAULT"
    holidays: set[date] = field(default_factory=set)
    sessions: list[TradingSession] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name:
            raise CalendarError("Calendar name cannot be empty.")

    def is_weekend(self, value: date) -> bool:
        """判断是否为周末。"""
        return value.weekday() >= 5

    def is_holiday(self, value: date) -> bool:
        """判断是否为假日。"""
        return value in self.holidays

    def is_trading_day(self, value: date) -> bool:
        """判断是否为交易日。"""
        return not self.is_weekend(value) and not self.is_holiday(value)

    def next_trading_day(
        self,
        value: date,
    ) -> date:
        """获取下一个交易日。"""
        current = value

        for _ in range(3660):
            current = date.fromordinal(current.toordinal() + 1)

            if self.is_trading_day(current):
                return current

        raise CalendarError(
            f"Unable to find next trading day after {value}."
        )

    def previous_trading_day(
        self,
        value: date,
    ) -> date:
        """获取上一个交易日。"""
        current = value

        for _ in range(3660):
            current = date.fromordinal(current.toordinal() - 1)

            if self.is_trading_day(current):
                return current

        raise CalendarError(
            f"Unable to find previous trading day before {value}."
        )

    def trading_days(
        self,
        start: date,
        end: date,
    ) -> list[date]:
        """返回指定日期范围内的所有交易日。"""
        if end < start:
            raise CalendarError(
                "End date cannot be earlier than start date."
            )

        result: list[date] = []
        current = start

        while current <= end:
            if self.is_trading_day(current):
                result.append(current)

            current = date.fromordinal(
                current.toordinal() + 1
            )

        return result

    def is_in_session(
        self,
        value: datetime,
        session_name: str | None = None,
    ) -> bool:
        """
        判断 datetime 是否处于交易时段。

        注意：
            这里不负责时区转换。
            调用者应先将时间转换到目标交易所时区。
        """
        if not self.is_trading_day(value.date()):
            return False

        for session in self.sessions:
            if session_name is not None and session.name != session_name:
                continue

            if session.open_time <= value.time() <= session.close_time:
                return True

        return False

    def add_holidays(
        self,
        holidays: Iterable[date],
    ) -> None:
        """增加假日。"""
        self.holidays.update(holidays)
