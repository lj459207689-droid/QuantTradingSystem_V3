"""
SQLite connection management for the quantitative trading system.

This module owns the physical connection to the local SQLite database
and provides a thin, dependency-free execution layer (no ORM).
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional, Sequence, Union


class DatabaseConnection:
    """
    Thin wrapper around Python's built-in sqlite3 module.

    Responsibilities
    ----------------
    - Own the database file path and connection lifecycle.
    - Provide execute / executemany / fetch helpers.
    - Provide a transaction context manager.
    - Apply pragmas sensible for a single-process trading system.

    This class does NOT know about business schema (see models.py)
    and does NOT know about specific entities (see repository.py).
    """

    def __init__(
        self,
        db_path: Union[str, Path] = "data/database/quant_system.db",
        check_same_thread: bool = True,
    ) -> None:

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.check_same_thread = check_same_thread

        self._connection: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """
        Return the underlying sqlite3 connection, creating it lazily.
        """

        if self._connection is None:
            self._connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=self.check_same_thread,
            )
            self._connection.row_factory = sqlite3.Row

            self._apply_pragmas(self._connection)

        return self._connection

    @staticmethod
    def _apply_pragmas(connection: sqlite3.Connection) -> None:
        """Apply pragmas suitable for a single-writer trading system."""

        connection.execute("PRAGMA foreign_keys = ON;")
        connection.execute("PRAGMA journal_mode = WAL;")
        connection.execute("PRAGMA synchronous = NORMAL;")

    def close(self) -> None:
        """Close the underlying connection, if open."""

        if self._connection is not None:
            self._connection.close()
            self._connection = None

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """
        Context manager providing an explicit transaction.

        Commits on success, rolls back on any exception.
        """

        connection = self.connect()

        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    def execute(
        self,
        sql: str,
        params: Sequence[Any] = (),
    ) -> sqlite3.Cursor:
        """Execute a single statement and commit immediately."""

        connection = self.connect()

        cursor = connection.execute(sql, params)
        connection.commit()

        return cursor

    def execute_many(
        self,
        sql: str,
        params_list: Iterable[Sequence[Any]],
    ) -> sqlite3.Cursor:
        """Execute the same statement for many parameter sets."""

        connection = self.connect()

        cursor = connection.executemany(sql, params_list)
        connection.commit()

        return cursor

    def fetch_one(
        self,
        sql: str,
        params: Sequence[Any] = (),
    ) -> Optional[sqlite3.Row]:
        """Execute a SELECT and return the first row, or None."""

        connection = self.connect()

        cursor = connection.execute(sql, params)
        return cursor.fetchone()

    def fetch_all(
        self,
        sql: str,
        params: Sequence[Any] = (),
    ) -> list[sqlite3.Row]:
        """Execute a SELECT and return all rows."""

        connection = self.connect()

        cursor = connection.execute(sql, params)
        return cursor.fetchall()

    def table_exists(self, table_name: str) -> bool:
        """Check whether a table exists in the database."""

        row = self.fetch_one(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name = ?
            """,
            (table_name,),
        )

        return row is not None

    def __enter__(self) -> "DatabaseConnection":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
