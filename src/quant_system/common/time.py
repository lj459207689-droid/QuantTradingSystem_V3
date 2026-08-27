"""
QuantTradingSystem V3
Common Time Utilities

统一时间、时区和时间戳处理。

原则：
    内部时间优先使用 timezone-aware datetime。
    系统内部推荐使用 UTC。
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

UTC = timezone.utc

NEW_YORK = ZoneInfo("America/New_York")
DAR_ES_SALAAM = ZoneInfo("Africa/Dar_es_Salaam")


def now_utc() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(UTC)


def today_utc() -> date:
    """返回当前 UTC 日期。"""
    return now_utc().date()


def ensure_aware(dt: datetime) -> datetime:
    """
    确保 datetime 为 timezone-aware。

    对 naive datetime 直接抛出异常，避免隐式时区错误。
    """
    if dt.tzinfo is None:
        raise ValueError(
            "Naive datetime is not allowed. "
            "Use a timezone-aware datetime."
        )

    return dt


def to_utc(dt: datetime) -> datetime:
    """将 datetime 转换为 UTC。"""
    ensure_aware(dt)
    return dt.astimezone(UTC)


def to_timezone(
    dt: datetime,
    timezone_name: str,
) -> datetime:
    """
    将 datetime 转换到指定时区。

    Parameters
    ----------
    dt:
        timezone-aware datetime。

    timezone_name:
        IANA timezone name，例如:
        America/New_York
        Africa/Dar_es_Salaam
    """
    ensure_aware(dt)

    return dt.astimezone(ZoneInfo(timezone_name))


def timestamp_to_datetime(
    timestamp: float,
    tz: timezone | ZoneInfo = UTC,
) -> datetime:
    """Unix timestamp 转 timezone-aware datetime。"""
    return datetime.fromtimestamp(timestamp, tz=tz)


def datetime_to_timestamp(dt: datetime) -> float:
    """timezone-aware datetime 转 Unix timestamp。"""
    ensure_aware(dt)
    return dt.timestamp()


def parse_iso_datetime(value: str) -> datetime:
    """
    解析 ISO 8601 datetime。

    支持：
        2026-08-16T12:30:00+00:00
        2026-08-16T12:30:00Z
    """
    normalized = value.strip()

    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    dt = datetime.fromisoformat(normalized)

    return ensure_aware(dt)


def format_iso_datetime(dt: datetime) -> str:
    """将 datetime 转换为 ISO 8601 字符串。"""
    ensure_aware(dt)
    return dt.isoformat()


def combine_date_time(
    value_date: date,
    value_time: time,
    tz: timezone | ZoneInfo = UTC,
) -> datetime:
    """将 date 和 time 组合为 timezone-aware datetime。"""
    return datetime.combine(
        value_date,
        value_time,
        tzinfo=tz,
    )


def start_of_day(
    value: datetime,
    tz: timezone | ZoneInfo | None = None,
) -> datetime:
    """返回指定日期的开始时间。"""
    ensure_aware(value)

    if tz is not None:
        value = value.astimezone(tz)

    return value.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )


def end_of_day(
    value: datetime,
    tz: timezone | ZoneInfo | None = None,
) -> datetime:
    """返回指定日期的结束时间。"""
    return start_of_day(value, tz) + timedelta(days=1) - timedelta(
        microseconds=1
    )
