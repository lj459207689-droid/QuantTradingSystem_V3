"""
Parquet-based market data storage.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .base import DataStorage


class ParquetStorage(DataStorage):
    """
    Store market data as Parquet files.

    Each storage key maps to one Parquet file.
    """

    def __init__(
        self,
        root: str | Path = "data",
    ) -> None:
        """
        Initialize Parquet storage.

        Parameters
        ----------
        root:
            Root directory used for storing Parquet files.
        """

        self.root = Path(root)
        self.root.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _path(
        self,
        key: str,
    ) -> Path:
        """
        Convert a storage key into a Parquet path.
        """

        if not key:
            raise ValueError(
                "key must not be empty"
            )

        path = self.root / f"{key}.parquet"

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        return path

    def save(
        self,
        key: str,
        data: pd.DataFrame,
    ) -> None:
        """
        Save market data to a Parquet file.
        """

        if data is None:
            raise ValueError(
                "data must not be None"
            )

        path = self._path(key)

        data.to_parquet(
            path,
            index=False,
        )

    def load(
        self,
        key: str,
    ) -> pd.DataFrame:
        """
        Load market data from a Parquet file.
        """

        path = self._path(key)

        if not path.exists():
            raise FileNotFoundError(
                f"Stored data not found: {path}"
            )

        return pd.read_parquet(path)

    def exists(
        self,
        key: str,
    ) -> bool:
        """
        Check whether a Parquet file exists.
        """

        return self._path(key).exists()
