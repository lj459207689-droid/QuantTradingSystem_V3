"""
QuantTradingSystem V3
Common Package
"""

from .calendar import TradingCalendar, TradingSession
from .exceptions import (
    BacktestError,
    CalendarError,
    ConfigurationError,
    ConnectionError,
    DatabaseError,
    DataError,
    ExecutionError,
    ModelError,
    QuantSystemError,
    RiskError,
    SerializationError,
    StrategyError,
    ValidationError,
)
from .logger import (
    close_logger,
    configure_logger,
    get_logger,
    set_level,
)
from .serialization import (
    dump_json,
    from_json,
    load_json,
    serialize,
    to_json,
)
from .time import (
    DAR_ES_SALAAM,
    NEW_YORK,
    UTC,
    datetime_to_timestamp,
    end_of_day,
    ensure_aware,
    format_iso_datetime,
    now_utc,
    parse_iso_datetime,
    start_of_day,
    timestamp_to_datetime,
    to_timezone,
    to_utc,
)
from .utils import (
    chunks,
    clamp,
    first_not_none,
    flatten,
    safe_float,
    safe_int,
)
from .validators import (
    validate_date_range,
    validate_instance,
    validate_non_negative,
    validate_not_empty,
    validate_not_none,
    validate_percentage,
    validate_positive,
    validate_range,
)

__all__ = [
    # Calendar
    "TradingCalendar",
    "TradingSession",

    # Exceptions
    "QuantSystemError",
    "ConfigurationError",
    "ValidationError",
    "DataError",
    "ConnectionError",
    "SerializationError",
    "ExecutionError",
    "RiskError",
    "StrategyError",
    "ModelError",
    "BacktestError",
    "DatabaseError",
    "CalendarError",

    # Logger
    "get_logger",
    "configure_logger",
    "set_level",
    "close_logger",

    # Serialization
    "serialize",
    "to_json",
    "from_json",
    "dump_json",
    "load_json",

    # Time
    "UTC",
    "NEW_YORK",
    "DAR_ES_SALAAM",
    "now_utc",
    "ensure_aware",
    "to_utc",
    "to_timezone",
    "timestamp_to_datetime",
    "datetime_to_timestamp",
    "parse_iso_datetime",
    "format_iso_datetime",
    "start_of_day",
    "end_of_day",

    # Validators
    "validate_not_none",
    "validate_not_empty",
    "validate_positive",
    "validate_non_negative",
    "validate_percentage",
    "validate_range",
    "validate_date_range",
    "validate_instance",

    # Utils
    "clamp",
    "chunks",
    "flatten",
    "first_not_none",
    "safe_float",
    "safe_int",
]
