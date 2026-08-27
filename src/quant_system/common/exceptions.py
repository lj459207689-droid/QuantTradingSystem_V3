"""
QuantTradingSystem V3
Common Exceptions

统一的系统异常体系。

依赖原则：
    common 不依赖 quant_system 的其他业务模块。
"""


class QuantSystemError(Exception):
    """所有量化交易系统异常的基类。"""

    def __init__(self, message: str = "Quant system error") -> None:
        self.message = message
        super().__init__(message)


class ConfigurationError(QuantSystemError):
    """配置错误。"""


class ValidationError(QuantSystemError):
    """参数或数据验证错误。"""


class DataError(QuantSystemError):
    """数据错误。"""


class ConnectionError(QuantSystemError):
    """外部服务连接错误。"""


class SerializationError(QuantSystemError):
    """序列化或反序列化错误。"""


class ExecutionError(QuantSystemError):
    """订单执行错误。"""


class RiskError(QuantSystemError):
    """风险控制错误。"""


class StrategyError(QuantSystemError):
    """策略运行错误。"""


class ModelError(QuantSystemError):
    """模型运行错误。"""


class BacktestError(QuantSystemError):
    """回测运行错误。"""


class DatabaseError(QuantSystemError):
    """数据库错误。"""


class CalendarError(QuantSystemError):
    """交易日历错误。"""
