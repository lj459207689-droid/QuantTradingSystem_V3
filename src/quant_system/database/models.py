"""
Database schema + serialization for the quantitative trading system.

This module is the bridge between core.entities (the domain model)
and SQLite storage. It owns:

- Table DDL, matched field-for-field to core.entities.
- serialize()/deserialize() functions that convert between entity
  dataclasses (with Enums, dates, and datetimes) and flat
  SQL-storable rows.

Deliberate deviations from the entity dataclasses (documented inline):

- Position: primary key is `contract_key` (a single TEXT column,
  computed from Position.contract_key) rather than a composite of
  nullable columns. This correctly distinguishes multiple option
  contracts on the same underlying (different expiry/strike/right),
  which a plain (symbol, direction) key could not.
- Account: core.entities.Account has no timestamp field. We add a
  DB-only `updated_at` column, populated by the repository.
- Signal: core.entities.Signal has no identifier field. We add a
  DB-only autoincrement `id` primary key; never round-tripped back
  into the Signal dataclass.
- Portfolio: core.entities.Portfolio bundles live Position objects
  in a dict, which does not belong in a single flat row. We persist
  a lightweight PortfolioSnapshot (account_id, balance, available,
  frozen, pnl totals, snapshot_at) instead; positions are read
  separately from the positions table.

Column-naming note: `"offset"` and `"direction"` are quoted with
double quotes everywhere in DDL/SQL because `OFFSET` is a SQL
keyword (used in LIMIT ... OFFSET ...) and could otherwise conflict
with hand-written or dynamically-built SQL.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, Optional

from quant_system.core.entities.account import Account
from quant_system.core.entities.fill import Fill
from quant_system.core.entities.order import (
    Direction,
    Offset,
    Order,
    OrderStatus,
    OrderType,
    SecurityType,
    TimeInForce,
)
from quant_system.core.entities.position import Position
from quant_system.core.entities.signal import Signal
from quant_system.core.entities.trade import Trade

# ---------------------------------------------------------------------------
# Small (de)serialization helpers
# ---------------------------------------------------------------------------


def _dt_to_iso(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if value is not None else None


def _iso_to_dt(value: Optional[str]) -> Optional[datetime]:
    return datetime.fromisoformat(value) if value else None


def _date_to_iso(value: Optional[date]) -> Optional[str]:
    return value.isoformat() if value is not None else None


def _iso_to_date(value: Optional[str]) -> Optional[date]:
    return date.fromisoformat(value) if value else None


def _enum_value(value: Any) -> Any:
    """Return .value for Enum members, pass through plain values."""
    return value.value if hasattr(value, "value") else value


# ---------------------------------------------------------------------------
# Table DDL
# ---------------------------------------------------------------------------

ORDERS_TABLE = """
CREATE TABLE IF NOT EXISTS orders (
    order_id        TEXT PRIMARY KEY,
    symbol          TEXT NOT NULL,
    security_type   TEXT NOT NULL DEFAULT 'STK',
    con_id          INTEGER,
    exchange        TEXT NOT NULL DEFAULT 'SMART',
    currency        TEXT NOT NULL DEFAULT 'USD',
    expiry          TEXT,
    strike          REAL,
    "right"         TEXT,
    multiplier      REAL,
    contract_key    TEXT NOT NULL,
    "direction"     TEXT NOT NULL,
    "offset"        TEXT NOT NULL,
    volume          REAL NOT NULL,
    price           REAL NOT NULL DEFAULT 0,
    stop_price      REAL,
    order_type      TEXT NOT NULL,
    time_in_force   TEXT NOT NULL DEFAULT 'DAY',
    strategy_id     TEXT,
    ib_order_id     INTEGER,
    perm_id         INTEGER,
    traded_volume   REAL NOT NULL DEFAULT 0,
    status          TEXT NOT NULL,
    create_time     TEXT NOT NULL,
    update_time     TEXT
);
"""

ORDERS_INDEXES = [
    'CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol);',
    'CREATE INDEX IF NOT EXISTS idx_orders_strategy ON orders(strategy_id);',
    'CREATE INDEX IF NOT EXISTS idx_orders_contract ON orders(contract_key);',
]

FILLS_TABLE = """
CREATE TABLE IF NOT EXISTS fills (
    fill_id         TEXT PRIMARY KEY,
    symbol          TEXT NOT NULL,
    security_type   TEXT NOT NULL DEFAULT 'STK',
    con_id          INTEGER,
    exchange        TEXT NOT NULL DEFAULT 'SMART',
    currency        TEXT NOT NULL DEFAULT 'USD',
    expiry          TEXT,
    strike          REAL,
    "right"         TEXT,
    multiplier      REAL,
    contract_key    TEXT NOT NULL,
    order_id        TEXT NOT NULL,
    ib_exec_id      TEXT,
    "direction"     TEXT NOT NULL,
    "offset"        TEXT NOT NULL,
    price           REAL NOT NULL,
    volume          REAL NOT NULL,
    commission      REAL NOT NULL DEFAULT 0,
    fill_time       TEXT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders (order_id)
);
"""

FILLS_INDEXES = [
    # Partial unique index: dedupe IBKR execIds without blocking
    # fills that don't have one (e.g. from other/simulated brokers).
    (
        'CREATE UNIQUE INDEX IF NOT EXISTS idx_fills_ib_exec_id '
        'ON fills(ib_exec_id) WHERE ib_exec_id IS NOT NULL;'
    ),
    'CREATE INDEX IF NOT EXISTS idx_fills_order ON fills(order_id);',
    'CREATE INDEX IF NOT EXISTS idx_fills_contract ON fills(contract_key);',
]

TRADES_TABLE = """
CREATE TABLE IF NOT EXISTS trades (
    trade_id        TEXT PRIMARY KEY,
    symbol          TEXT NOT NULL,
    side            TEXT NOT NULL,
    quantity        REAL NOT NULL,
    price           REAL NOT NULL,
    timestamp       TEXT NOT NULL,
    commission      REAL NOT NULL DEFAULT 0,
    realized_pnl    REAL NOT NULL DEFAULT 0,
    order_id        TEXT
);
"""

POSITIONS_TABLE = """
CREATE TABLE IF NOT EXISTS positions (
    contract_key    TEXT PRIMARY KEY,
    symbol          TEXT NOT NULL,
    security_type   TEXT NOT NULL DEFAULT 'STK',
    con_id          INTEGER,
    exchange        TEXT NOT NULL DEFAULT 'SMART',
    currency        TEXT NOT NULL DEFAULT 'USD',
    expiry          TEXT,
    strike          REAL,
    "right"         TEXT,
    multiplier      REAL,
    "direction"     TEXT NOT NULL,
    volume          REAL NOT NULL DEFAULT 0,
    frozen          REAL NOT NULL DEFAULT 0,
    price           REAL NOT NULL DEFAULT 0,
    pnl             REAL NOT NULL DEFAULT 0,
    realized_pnl    REAL NOT NULL DEFAULT 0,
    last_update     TEXT NOT NULL
);
"""

POSITIONS_INDEXES = [
    'CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);',
]

ACCOUNTS_TABLE = """
CREATE TABLE IF NOT EXISTS accounts (
    account_id      TEXT PRIMARY KEY,
    cash            REAL NOT NULL DEFAULT 0,
    buying_power    REAL NOT NULL DEFAULT 0,
    equity          REAL NOT NULL DEFAULT 0,
    realized_pnl    REAL NOT NULL DEFAULT 0,
    unrealized_pnl  REAL NOT NULL DEFAULT 0,
    updated_at      TEXT NOT NULL
);
"""

SIGNALS_TABLE = """
CREATE TABLE IF NOT EXISTS signals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol          TEXT NOT NULL,
    signal          TEXT NOT NULL,
    timestamp       TEXT NOT NULL,
    strength        REAL NOT NULL DEFAULT 0,
    price           REAL,
    metadata        TEXT
);
"""

PORTFOLIO_SNAPSHOTS_TABLE = """
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id          TEXT NOT NULL,
    balance             REAL NOT NULL DEFAULT 0,
    available           REAL NOT NULL DEFAULT 0,
    frozen              REAL NOT NULL DEFAULT 0,
    unrealized_pnl      REAL,
    realized_pnl        REAL,
    snapshot_at         TEXT NOT NULL
);
"""

PORTFOLIO_SNAPSHOTS_INDEXES = [
    (
        'CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_account '
        'ON portfolio_snapshots(account_id, snapshot_at);'
    ),
]

SCHEMA_MIGRATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version         INTEGER PRIMARY KEY,
    applied_at      TEXT NOT NULL
);
"""

# Ordered so foreign-key parents are created before children.
TABLE_SCHEMAS: list[tuple[str, str]] = [
    ("schema_migrations", SCHEMA_MIGRATIONS_TABLE),
    ("orders", ORDERS_TABLE),
    ("fills", FILLS_TABLE),
    ("trades", TRADES_TABLE),
    ("positions", POSITIONS_TABLE),
    ("accounts", ACCOUNTS_TABLE),
    ("signals", SIGNALS_TABLE),
    ("portfolio_snapshots", PORTFOLIO_SNAPSHOTS_TABLE),
]

ALL_INDEXES: list[str] = [
    *ORDERS_INDEXES,
    *FILLS_INDEXES,
    *POSITIONS_INDEXES,
    *PORTFOLIO_SNAPSHOTS_INDEXES,
]


def create_all(connection: sqlite3.Connection) -> None:
    """Create every table and index if it does not exist."""

    for _, ddl in TABLE_SCHEMAS:
        connection.execute(ddl)

    for index_ddl in ALL_INDEXES:
        connection.execute(index_ddl)

    connection.commit()


# ---------------------------------------------------------------------------
# Order <-> row
# ---------------------------------------------------------------------------


def order_to_params(order: Order) -> Dict[str, Any]:
    if not order.order_id:
        raise ValueError("Order.order_id must be set before persisting")

    return {
        "order_id": order.order_id,
        "symbol": order.symbol,
        "security_type": _enum_value(order.security_type),
        "con_id": order.con_id,
        "exchange": order.exchange,
        "currency": order.currency,
        "expiry": _date_to_iso(order.expiry),
        "strike": order.strike,
        "right": order.right,
        "multiplier": order.multiplier,
        "contract_key": order.contract_key,
        "direction": _enum_value(order.direction),
        "offset": _enum_value(order.offset),
        "volume": order.volume,
        "price": order.price,
        "stop_price": order.stop_price,
        "order_type": _enum_value(order.order_type),
        "time_in_force": _enum_value(order.time_in_force),
        "strategy_id": order.strategy_id,
        "ib_order_id": order.ib_order_id,
        "perm_id": order.perm_id,
        "traded_volume": order.traded_volume,
        "status": _enum_value(order.status),
        "create_time": _dt_to_iso(order.create_time),
        "update_time": _dt_to_iso(order.update_time),
    }


def order_from_row(row: sqlite3.Row) -> Order:
    return Order(
        symbol=row["symbol"],
        security_type=SecurityType(row["security_type"]),
        con_id=row["con_id"],
        exchange=row["exchange"],
        currency=row["currency"],
        expiry=_iso_to_date(row["expiry"]),
        strike=row["strike"],
        right=row["right"],
        multiplier=row["multiplier"],
        direction=Direction(row["direction"]),
        offset=Offset(row["offset"]),
        volume=row["volume"],
        price=row["price"],
        stop_price=row["stop_price"],
        order_type=OrderType(row["order_type"]),
        time_in_force=TimeInForce(row["time_in_force"]),
        order_id=row["order_id"],
        strategy_id=row["strategy_id"],
        ib_order_id=row["ib_order_id"],
        perm_id=row["perm_id"],
        traded_volume=row["traded_volume"],
        status=OrderStatus(row["status"]),
        create_time=_iso_to_dt(row["create_time"]),
        update_time=_iso_to_dt(row["update_time"]),
    )


# ---------------------------------------------------------------------------
# Fill <-> row
# ---------------------------------------------------------------------------


def fill_to_params(fill: Fill) -> Dict[str, Any]:
    return {
        "fill_id": fill.fill_id,
        "symbol": fill.symbol,
        "security_type": _enum_value(fill.security_type),
        "con_id": fill.con_id,
        "exchange": fill.exchange,
        "currency": fill.currency,
        "expiry": _date_to_iso(fill.expiry),
        "strike": fill.strike,
        "right": fill.right,
        "multiplier": fill.multiplier,
        "contract_key": fill.contract_key,
        "order_id": fill.order_id,
        "ib_exec_id": fill.ib_exec_id,
        "direction": _enum_value(fill.direction),
        "offset": _enum_value(fill.offset),
        "price": fill.price,
        "volume": fill.volume,
        "commission": fill.commission,
        "fill_time": _dt_to_iso(fill.fill_time),
    }


def fill_from_row(row: sqlite3.Row) -> Fill:
    return Fill(
        symbol=row["symbol"],
        security_type=SecurityType(row["security_type"]),
        con_id=row["con_id"],
        exchange=row["exchange"],
        currency=row["currency"],
        expiry=_iso_to_date(row["expiry"]),
        strike=row["strike"],
        right=row["right"],
        multiplier=row["multiplier"],
        order_id=row["order_id"],
        fill_id=row["fill_id"],
        ib_exec_id=row["ib_exec_id"],
        direction=Direction(row["direction"]),
        offset=Offset(row["offset"]),
        price=row["price"],
        volume=row["volume"],
        commission=row["commission"],
        fill_time=_iso_to_dt(row["fill_time"]),
    )


# ---------------------------------------------------------------------------
# Trade <-> row (entity unchanged from before)
# ---------------------------------------------------------------------------


def trade_to_params(trade: Trade) -> Dict[str, Any]:
    return {
        "trade_id": trade.trade_id,
        "symbol": trade.symbol,
        "side": trade.side,
        "quantity": trade.quantity,
        "price": trade.price,
        "timestamp": _dt_to_iso(trade.timestamp),
        "commission": trade.commission,
        "realized_pnl": trade.realized_pnl,
        "order_id": trade.order_id,
    }


def trade_from_row(row: sqlite3.Row) -> Trade:
    return Trade(
        trade_id=row["trade_id"],
        symbol=row["symbol"],
        side=row["side"],
        quantity=row["quantity"],
        price=row["price"],
        timestamp=_iso_to_dt(row["timestamp"]),
        commission=row["commission"],
        realized_pnl=row["realized_pnl"],
        order_id=row["order_id"],
    )


# ---------------------------------------------------------------------------
# Position <-> row
# ---------------------------------------------------------------------------


def position_to_params(position: Position) -> Dict[str, Any]:
    return {
        "contract_key": position.contract_key,
        "symbol": position.symbol,
        "security_type": _enum_value(position.security_type),
        "con_id": position.con_id,
        "exchange": position.exchange,
        "currency": position.currency,
        "expiry": _date_to_iso(position.expiry),
        "strike": position.strike,
        "right": position.right,
        "multiplier": position.multiplier,
        "direction": _enum_value(position.direction),
        "volume": position.volume,
        "frozen": position.frozen,
        "price": position.price,
        "pnl": position.pnl,
        "realized_pnl": position.realized_pnl,
        "last_update": _dt_to_iso(position.last_update),
    }


def position_from_row(row: sqlite3.Row) -> Position:
    return Position(
        symbol=row["symbol"],
        security_type=SecurityType(row["security_type"]),
        con_id=row["con_id"],
        exchange=row["exchange"],
        currency=row["currency"],
        expiry=_iso_to_date(row["expiry"]),
        strike=row["strike"],
        right=row["right"],
        multiplier=row["multiplier"],
        direction=Direction(row["direction"]),
        volume=row["volume"],
        frozen=row["frozen"],
        price=row["price"],
        pnl=row["pnl"],
        realized_pnl=row["realized_pnl"],
        last_update=_iso_to_dt(row["last_update"]),
    )


# ---------------------------------------------------------------------------
# Account <-> row
# ---------------------------------------------------------------------------


def account_to_params(
    account: Account,
    updated_at: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "account_id": account.account_id,
        "cash": account.cash,
        "buying_power": account.buying_power,
        "equity": account.equity,
        "realized_pnl": account.realized_pnl,
        "unrealized_pnl": account.unrealized_pnl,
        "updated_at": updated_at or datetime.now().isoformat(),
    }


def account_from_row(row: sqlite3.Row) -> Account:
    return Account(
        account_id=row["account_id"],
        cash=row["cash"],
        buying_power=row["buying_power"],
        equity=row["equity"],
        realized_pnl=row["realized_pnl"],
        unrealized_pnl=row["unrealized_pnl"],
    )


# ---------------------------------------------------------------------------
# Signal <-> row (no natural id on the entity; DB id is not round-tripped)
# ---------------------------------------------------------------------------


def signal_to_params(signal: Signal) -> Dict[str, Any]:
    return {
        "symbol": signal.symbol,
        "signal": signal.signal,
        "timestamp": _dt_to_iso(signal.timestamp),
        "strength": signal.strength,
        "price": signal.price,
        "metadata": json.dumps(signal.metadata or {}),
    }


def signal_from_row(row: sqlite3.Row) -> Signal:
    metadata = json.loads(row["metadata"]) if row["metadata"] else {}

    return Signal(
        symbol=row["symbol"],
        signal=row["signal"],
        timestamp=_iso_to_dt(row["timestamp"]),
        strength=row["strength"],
        price=row["price"],
        metadata=metadata,
    )


# ---------------------------------------------------------------------------
# Portfolio snapshot (DB-only lightweight model; positions live separately)
# ---------------------------------------------------------------------------


@dataclass
class PortfolioSnapshot:
    """
    A point-in-time snapshot of Portfolio-level balances.

    This intentionally excludes `positions` (core.entities.Portfolio's
    dict of live Position objects) - those are read from the positions
    table directly via PositionRepository.

    unrealized_pnl / realized_pnl mirror Portfolio.total_pnl /
    Portfolio.total_realized_pnl at the moment of the snapshot, so an
    equity curve can be reconstructed without replaying positions
    history.
    """

    account_id: str
    balance: float
    available: float
    frozen: float
    snapshot_at: datetime
    unrealized_pnl: Optional[float] = None
    realized_pnl: Optional[float] = None
    id: Optional[int] = None


def portfolio_snapshot_to_params(snapshot: PortfolioSnapshot) -> Dict[str, Any]:
    return {
        "account_id": snapshot.account_id,
        "balance": snapshot.balance,
        "available": snapshot.available,
        "frozen": snapshot.frozen,
        "unrealized_pnl": snapshot.unrealized_pnl,
        "realized_pnl": snapshot.realized_pnl,
        "snapshot_at": _dt_to_iso(snapshot.snapshot_at),
    }


def portfolio_snapshot_from_row(row: sqlite3.Row) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        id=row["id"],
        account_id=row["account_id"],
        balance=row["balance"],
        available=row["available"],
        frozen=row["frozen"],
        unrealized_pnl=row["unrealized_pnl"],
        realized_pnl=row["realized_pnl"],
        snapshot_at=_iso_to_dt(row["snapshot_at"]),
    )
