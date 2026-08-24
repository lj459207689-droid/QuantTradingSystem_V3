"""
Quant Trading System - Database Module.

Persistence layer for orders, trades, fills, positions, accounts,
and signals. Built on plain sqlite3 (no ORM). Historical/realtime
market data stays in the 03_data module (parquet/storage), this
module is for transactional/system-of-record data.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

from .connection import DatabaseConnection
from .migrations import apply_migrations, get_current_version
from .repository import (
    AccountRepository,
    FillRepository,
    OrderRepository,
    PortfolioSnapshotRepository,
    PositionRepository,
    SignalRepository,
    TradeRepository,
)

__all__ = [
    "Database",
    "DatabaseConnection",
    "OrderRepository",
    "TradeRepository",
    "FillRepository",
    "PositionRepository",
    "AccountRepository",
    "SignalRepository",
    "PortfolioSnapshotRepository",
]


class Database:
    """
    Composition root for the database module.

    Owns the connection, runs migrations on construction, and exposes
    one repository per entity. This is the intended entry point for
    the rest of the system, analogous to data.manager.DataManager for
    the 03_data module.
    """

    def __init__(
        self,
        db_path: Union[str, Path] = "data/database/quant_system.db",
        auto_migrate: bool = True,
    ) -> None:

        self.connection = DatabaseConnection(db_path)

        if auto_migrate:
            apply_migrations(self.connection)

        self.orders = OrderRepository(self.connection)
        self.trades = TradeRepository(self.connection)
        self.fills = FillRepository(self.connection)
        self.positions = PositionRepository(self.connection)
        self.accounts = AccountRepository(self.connection)
        self.signals = SignalRepository(self.connection)
        self.portfolio_snapshots = PortfolioSnapshotRepository(self.connection)

    def schema_version(self) -> int:
        """Return the currently applied schema version."""
        return get_current_version(self.connection)

    def close(self) -> None:
        """Close the underlying connection."""
        self.connection.close()

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
