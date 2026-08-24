# src/quant_system/core/interfaces/data_provider.py

from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict
from datetime import datetime
import pandas as pd
from quant_system.core.entities import Bar, Tick


class BaseDataProvider(ABC):
    """
    数据提供者抽象接口 [cite: 20, 24]
    支持从 Polygon, Databento, ClickHouse, Local Parquet 读取历史 1s Bar / Tick 数据 [cite: 23, 24, 25]
    """

    @abstractmethod
    def connect(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """建立数据源连接 (数据库、REST/gRPC 接口等) [cite: 25]"""
        pass

    @abstractmethod
    def get_historical_bars(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        timeframe: str = "1s"
    ) -> List[Bar]:
        """
        拉取历史 Bar 列表 (常用于策略 on_init 时的因子滑动窗口预热) [cite: 25, 29]
        """
        pass

    @abstractmethod
    def get_historical_ticks(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Tick]:
        """拉取指定时间段的高频 Tick 深度历史数据 [cite: 26]"""
        pass

    @abstractmethod
    def get_df_bars(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        timeframe: str = "1s"
    ) -> pd.DataFrame:
        """
        获取 DataFrame 格式数据，便于离线 ML 模型训练与批量因子计算 [cite: 27]
        """
        pass