"""
QuantTradingSystem V3
Common Logger

统一日志基础设施。

设计原则：
    1. Common 不依赖 ConfigManager。
    2. 不依赖 core/data/risk/execution 等业务模块。
    3. 支持控制台和文件日志。
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


DEFAULT_FORMAT = (
    "%(asctime)s | "
    "%(levelname)s | "
    "%(name)s | "
    "%(message)s"
)


def get_logger(name: str = "quant_system") -> logging.Logger:
    """
    获取 Logger。

    Parameters
    ----------
    name:
        Logger 名称。

    Returns
    -------
    logging.Logger
    """
    return logging.getLogger(name)


def configure_logger(
    name: str = "quant_system",
    level: int = logging.INFO,
    log_file: str | Path | None = None,
    console: bool = True,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> logging.Logger:
    """
    配置系统 Logger。

    Parameters
    ----------
    name:
        Logger 名称。

    level:
        日志级别。

    log_file:
        日志文件路径。

    console:
        是否输出到控制台。

    max_bytes:
        单个日志文件最大大小。

    backup_count:
        保留的日志文件数量。

    Returns
    -------
    logging.Logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    formatter = logging.Formatter(DEFAULT_FORMAT)

    if not logger.handlers:
        if console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        if log_file is not None:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )

            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def set_level(
    logger: logging.Logger,
    level: int,
) -> None:
    """修改 Logger 日志级别。"""
    logger.setLevel(level)


def close_logger(logger: logging.Logger) -> None:
    """
    关闭 Logger 的所有 Handler。

    主要用于测试、程序退出和重新初始化。
    """
    handlers = logger.handlers[:]

    for handler in handlers:
        handler.close()
        logger.removeHandler(handler)