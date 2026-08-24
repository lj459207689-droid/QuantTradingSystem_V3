"""
Repository layer for the quantitative trading system.

Each repository wraps hand-written SQL for one table and returns the
matching core.entities dataclass (or, for Signal/PortfolioSnapshot,
a small DB-only model - see models.py for why). No ORM is used.

All dynamically-built column names are double-quoted (see
_quote()) so that fields like Order.offset - which collides with
the SQL keyword OFFSET - never break query construction.
"""

from __future__ import annotations

from typing import Any, Callable, Generic, List, Optional, Tuple, TypeVar, Union

from quant_system.core.entities.account import Account
from quant_system.core.entities.fill import Fill
from quant_system.core.entities.order import Order
from quant_system.core.entities.position import Position
from quant_system.core.entities.signal import Signal
from quant_system.core.entities.trade import Trade

from .connection import DatabaseConnection
from .models import (
    PortfolioSnapshot,
    account_from_row,
    account_to_params,
    fill_from_row,
    fill_to_params,
    order_from_row,
    order_to_params,
    portfolio_snapshot_from_row,
    portfolio_snapshot_to_params,
    position_from_row,
    position_to_params,
    signal_from_row,
    signal_to_params,
    trade_from_row,
    trade_to_params,
)

EntityT = TypeVar("EntityT")


def _quote(column: str) -> str:
    """Double-quote a SQL identifier so keywords (e.g. OFFSET) are safe."""
    return f'"{column}"'


class BaseRepository(Generic[EntityT]):
    """
    Generic CRUD repository shared by every table-specific repository.

    Subclasses provide:
        table_name    physical table name
        id_columns    tuple of column names forming the primary key
        serialize     entity -> flat dict of column -> value
        deserialize   sqlite3.Row -> entity
    """

    table_name: str = ""
    id_columns: Tuple[str, ...] = ()

    serialize: Callable[[EntityT], dict] = staticmethod(lambda e: {})
    deserialize: Callable[[Any], EntityT] = staticmethod(lambda r: r)

    def __init__(self, connection: DatabaseConnection) -> None:
        self.connection = connection

    def _id_where_clause(self) -> str:
        return " AND ".join(f"{_quote(c)} = ?" for c in self.id_columns)

    @staticmethod
    def _normalize_ids(id_values: Union[Any, Tuple[Any, ...]]) -> Tuple[Any, ...]:
        return id_values if isinstance(id_values, tuple) else (id_values,)

    def insert(self, entity: EntityT) -> None:
        """Insert a new row."""

        data = self.serialize(entity)
        columns = list(data.keys())
        placeholders = ", ".join(["?"] * len(columns))
        quoted_columns = ", ".join(_quote(c) for c in columns)

        sql = (
            f"INSERT INTO {self.table_name} "
            f"({quoted_columns}) VALUES ({placeholders})"
        )

        self.connection.execute(sql, tuple(data[c] for c in columns))

    def upsert(self, entity: EntityT) -> None:
        """Insert a row, replacing any existing row with the same id."""

        data = self.serialize(entity)
        columns = list(data.keys())
        placeholders = ", ".join(["?"] * len(columns))
        quoted_columns = ", ".join(_quote(c) for c in columns)

        sql = (
            f"INSERT OR REPLACE INTO {self.table_name} "
            f"({quoted_columns}) VALUES ({placeholders})"
        )

        self.connection.execute(sql, tuple(data[c] for c in columns))

    def update(self, id_values: Union[Any, Tuple[Any, ...]], **fields) -> None:
        """Update specific columns for a row identified by its id."""

        if not fields:
            raise ValueError("update() requires at least one field")

        assignments = ", ".join(f"{_quote(c)} = ?" for c in fields)

        sql = (
            f"UPDATE {self.table_name} "
            f"SET {assignments} WHERE {self._id_where_clause()}"
        )

        params = tuple(fields.values()) + self._normalize_ids(id_values)

        self.connection.execute(sql, params)

    def delete(self, id_values: Union[Any, Tuple[Any, ...]]) -> None:
        """Delete a row by id."""

        sql = f"DELETE FROM {self.table_name} WHERE {self._id_where_clause()}"
        self.connection.execute(sql, self._normalize_ids(id_values))

    def find_by_id(
        self, id_values: Union[Any, Tuple[Any, ...]]
    ) -> Optional[EntityT]:
        """Fetch a single row by id, or None if not found."""

        sql = f"SELECT * FROM {self.table_name} WHERE {self._id_where_clause()}"
        row = self.connection.fetch_one(sql, self._normalize_ids(id_values))

        if row is None:
            return None

        return self.deserialize(row)

    def find_all(
        self,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
    ) -> List[EntityT]:
        """Fetch every row in the table, optionally ordered/limited."""

        sql = f"SELECT * FROM {self.table_name}"

        if order_by:
            sql += f" ORDER BY {_quote(order_by)}"

        if limit is not None:
            sql += f" LIMIT {int(limit)}"

        rows = self.connection.fetch_all(sql)

        return [self.deserialize(r) for r in rows]

    def find_where(
        self,
        column: str,
        value: Any,
        order_by: Optional[str] = None,
    ) -> List[EntityT]:
        """Fetch rows where a single column equals a value."""

        sql = f"SELECT * FROM {self.table_name} WHERE {_quote(column)} = ?"

        if order_by:
            sql += f" ORDER BY {_quote(order_by)}"

        rows = self.connection.fetch_all(sql, (value,))

        return [self.deserialize(r) for r in rows]

    def count(self) -> int:
        """Return the number of rows in the table."""

        row = self.connection.fetch_one(
            f"SELECT COUNT(*) AS n FROM {self.table_name}"
        )

        return int(row["n"]) if row is not None else 0

    def delete_where_older_than(
        self,
        timestamp_column: str,
        cutoff_iso: str,
    ) -> int:
        """
        Data lifecycle helper: delete rows whose timestamp column is
        older than the given ISO-8601 cutoff. Returns rows deleted.
        """

        cursor = self.connection.execute(
            f"DELETE FROM {self.table_name} "
            f"WHERE {_quote(timestamp_column)} < ?",
            (cutoff_iso,),
        )

        return cursor.rowcount


# ---------------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------------


class OrderRepository(BaseRepository[Order]):
    table_name = "orders"
    id_columns = ("order_id",)

    serialize = staticmethod(order_to_params)
    deserialize = staticmethod(order_from_row)

    def find_open_orders(self) -> List[Order]:
        """Orders not yet in a terminal state."""

        rows = self.connection.fetch_all(
            """
            SELECT * FROM orders
            WHERE status NOT IN ('ALLTRADED', 'CANCELLED', 'REJECTED')
            ORDER BY create_time
            """
        )

        return [order_from_row(r) for r in rows]

    def find_by_symbol(self, symbol: str) -> List[Order]:
        return self.find_where("symbol", symbol, order_by="create_time")

    def find_by_strategy(self, strategy_id: str) -> List[Order]:
        return self.find_where(
            "strategy_id", strategy_id, order_by="create_time"
        )

    def find_by_contract(self, contract_key: str) -> List[Order]:
        return self.find_where(
            "contract_key", contract_key, order_by="create_time"
        )


# ---------------------------------------------------------------------------
# Fill
# ---------------------------------------------------------------------------


class FillRepository(BaseRepository[Fill]):
    table_name = "fills"
    id_columns = ("fill_id",)

    serialize = staticmethod(fill_to_params)
    deserialize = staticmethod(fill_from_row)

    def find_by_order(self, order_id: str) -> List[Fill]:
        return self.find_where("order_id", order_id, order_by="fill_time")

    def find_by_contract(self, contract_key: str) -> List[Fill]:
        return self.find_where(
            "contract_key", contract_key, order_by="fill_time"
        )

    def exists_by_ib_exec_id(self, ib_exec_id: str) -> bool:
        """
        Check whether a fill with this IBKR execId has already been
        recorded - use before inserting to avoid duplicate fills when
        IBKR resends the same execution report.
        """

        row = self.connection.fetch_one(
            "SELECT 1 FROM fills WHERE ib_exec_id = ?",
            (ib_exec_id,),
        )

        return row is not None


# ---------------------------------------------------------------------------
# Trade (entity unchanged)
# ---------------------------------------------------------------------------


class TradeRepository(BaseRepository[Trade]):
    table_name = "trades"
    id_columns = ("trade_id",)

    serialize = staticmethod(trade_to_params)
    deserialize = staticmethod(trade_from_row)

    def find_by_order(self, order_id: str) -> List[Trade]:
        return self.find_where("order_id", order_id, order_by="timestamp")

    def find_by_symbol(self, symbol: str) -> List[Trade]:
        return self.find_where("symbol", symbol, order_by="timestamp")


# ---------------------------------------------------------------------------
# Position
# ---------------------------------------------------------------------------


class PositionRepository(BaseRepository[Position]):
    table_name = "positions"
    id_columns = ("contract_key",)

    serialize = staticmethod(position_to_params)
    deserialize = staticmethod(position_from_row)

    def upsert_position(self, position: Position) -> None:
        """Positions are naturally keyed by contract_key; upsert is the norm."""
        self.upsert(position)

    def find_by_contract_key(self, contract_key: str) -> Optional[Position]:
        return self.find_by_id(contract_key)

    def find_by_symbol(self, symbol: str) -> List[Position]:
        """
        All positions for a symbol - may be more than one under options
        (different expiry/strike/right) or when both a LONG and SHORT
        position coexist.
        """
        return self.find_where("symbol", symbol)


# ---------------------------------------------------------------------------
# Account
# ---------------------------------------------------------------------------


class AccountRepository(BaseRepository[Account]):
    table_name = "accounts"
    id_columns = ("account_id",)

    serialize = staticmethod(account_to_params)
    deserialize = staticmethod(account_from_row)

    def upsert_account(self, account: Account) -> None:
        """Convenience wrapper: upsert with a fresh updated_at timestamp."""
        self.upsert(account)


# ---------------------------------------------------------------------------
# Signal (no natural id on the entity - see models.py)
# ---------------------------------------------------------------------------


class SignalRepository(BaseRepository[Signal]):
    table_name = "signals"
    id_columns = ("id",)

    serialize = staticmethod(signal_to_params)
    deserialize = staticmethod(signal_from_row)

    def insert(self, entity: Signal) -> int:
        """
        Insert a signal and return the generated DB row id.

        Overridden (rather than using the generic insert()) because
        Signal has no id field to serialize - the column is
        autoincrement and only exists at the DB layer.
        """

        data = self.serialize(entity)
        columns = list(data.keys())
        placeholders = ", ".join(["?"] * len(columns))
        quoted_columns = ", ".join(_quote(c) for c in columns)

        sql = (
            f"INSERT INTO {self.table_name} "
            f"({quoted_columns}) VALUES ({placeholders})"
        )

        cursor = self.connection.execute(
            sql, tuple(data[c] for c in columns)
        )

        return cursor.lastrowid

    def find_by_symbol(self, symbol: str) -> List[Signal]:
        return self.find_where("symbol", symbol, order_by="timestamp")


# ---------------------------------------------------------------------------
# Portfolio snapshots
# ---------------------------------------------------------------------------


class PortfolioSnapshotRepository(BaseRepository[PortfolioSnapshot]):
    table_name = "portfolio_snapshots"
    id_columns = ("id",)

    serialize = staticmethod(portfolio_snapshot_to_params)
    deserialize = staticmethod(portfolio_snapshot_from_row)

    def insert(self, entity: PortfolioSnapshot) -> int:
        """Insert a snapshot and return the generated DB row id."""

        data = self.serialize(entity)
        columns = list(data.keys())
        placeholders = ", ".join(["?"] * len(columns))
        quoted_columns = ", ".join(_quote(c) for c in columns)

        sql = (
            f"INSERT INTO {self.table_name} "
            f"({quoted_columns}) VALUES ({placeholders})"
        )

        cursor = self.connection.execute(
            sql, tuple(data[c] for c in columns)
        )

        return cursor.lastrowid

    def find_latest(self, account_id: str) -> Optional[PortfolioSnapshot]:
        row = self.connection.fetch_one(
            """
            SELECT * FROM portfolio_snapshots
            WHERE account_id = ?
            ORDER BY snapshot_at DESC
            LIMIT 1
            """,
            (account_id,),
        )

        return portfolio_snapshot_from_row(row) if row is not None else None

    def find_by_account(self, account_id: str) -> List[PortfolioSnapshot]:
        return self.find_where(
            "account_id", account_id, order_by="snapshot_at"
        )
