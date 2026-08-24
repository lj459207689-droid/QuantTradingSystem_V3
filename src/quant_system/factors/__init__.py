"""
Factor subsystem.
"""

from .base import BaseFactor
from .pipeline import FactorPipeline
from .state import FactorState, RollingWindow
from .stream import FactorStream, FactorStreamResult
from .trend.ema import EMA
from .trend.sma import SMA

__all__ = [
    "BaseFactor",
    "FactorPipeline",
    "FactorState",
    "RollingWindow",
    "FactorStream",
    "FactorStreamResult",
    "EMA",
    "SMA",
]