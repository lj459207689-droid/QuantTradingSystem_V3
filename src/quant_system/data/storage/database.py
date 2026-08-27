"""
Database-based market data storage using Python's built-in sqlite3.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from .base import DataStorage


class DatabaseStorage(DataStorage):
    """
    Store market data in a local SQLite database file using Python built-in sqlite3.

    Each storage key maps to one SQLite table name.
    """

    def __init__(
        self,
        db_path: str | Path = "data/market_data.db",
    ) -> None:
        """
        Initialize SQLite Database storage.

        Parameters
        ----------
        db_path:
            Path to the SQLite database file.
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _table_name(self, key: str) -> str:
        """
        Convert a storage key into a valid database table name.
        """
        if not key:
            raise ValueError("key must not be empty")

        # 清理表名中的非法字符
        return key.replace("-", "_").replace(".", "_").replace("/", "_").lower()

    def save(
        self,
        key: str,
        data: pd.DataFrame,
    ) -> None:
        """
        Save market data DataFrame to a SQLite database table.
        """
        if data is None:
            raise ValueError("data must not be None")

        table_name = self._table_name(key)

        with sqlite3.connect(self.db_path) as conn:
            data.to_sql(
                name=table_name,
                con=conn,
                if_exists="replace",
                index=False,
                chunksize=5000,
            )

    def load(
        self,
        key: str,
    ) -> pd.DataFrame:
        """
        Load market data DataFrame from a SQLite database table.
        """
        table_name = self._table_name(key)

        if not self.exists(key):
            raise FileNotFoundError(
                f"Stored data table not found: {table_name}"
            )

        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(
                f"SELECT * FROM {table_name}",
                con=conn,
            )

    def exists(
        self,
        key: str,
    ) -> bool:
        """
        Check whether a SQLite database table exists.
        """
        table_name = self._table_name(key)

        if not self.db_path.exists():
            return False

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
                (table_name,),
            )
            return cursor.fetchone() is not None
