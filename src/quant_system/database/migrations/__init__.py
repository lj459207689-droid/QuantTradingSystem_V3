"""
Schema migration support for the database module.

This is intentionally minimal: a single "run everything in models.py"
migration (version 1), plus a schema_migrations table to track what
has been applied. Future schema changes should be added as new
numbered migrations in MIGRATIONS below.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Callable, List, Tuple

from ..connection import DatabaseConnection
from ..models import create_all


def _migration_001_initial_schema(connection: sqlite3.Connection) -> None:
    """Create all tables defined in models.py."""
    create_all(connection)


# Ordered list of (version, description, migration_function).
# Append new migrations here; never reorder or remove existing ones.
MIGRATIONS: List[Tuple[int, str, Callable[[sqlite3.Connection], None]]] = [
    (1, "initial_schema", _migration_001_initial_schema),
]


def get_current_version(connection: DatabaseConnection) -> int:
    """Return the highest applied migration version, or 0 if none."""

    if not connection.table_exists("schema_migrations"):
        return 0

    row = connection.fetch_one(
        "SELECT MAX(version) AS version FROM schema_migrations"
    )

    if row is None or row["version"] is None:
        return 0

    return int(row["version"])


def apply_migrations(connection: DatabaseConnection) -> List[int]:
    """
    Apply all pending migrations in order.

    Returns the list of migration versions that were applied.
    """

    current_version = get_current_version(connection)
    applied: List[int] = []

    for version, _description, migration_fn in MIGRATIONS:
        if version <= current_version:
            continue

        raw_connection = connection.connect()

        migration_fn(raw_connection)

        raw_connection.execute(
            "INSERT INTO schema_migrations (version, applied_at) "
            "VALUES (?, ?)",
            (version, datetime.now(timezone.utc).isoformat()),
        )
        raw_connection.commit()

        applied.append(version)

    return applied
