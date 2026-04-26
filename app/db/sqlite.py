import sqlite3
from pathlib import Path
from typing import Iterator

from fastapi import Request

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_id TEXT NOT NULL,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        department TEXT NOT NULL,
        location TEXT NOT NULL,
        position TEXT NOT NULL,
        phone TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS organization_column_config (
        organization_id TEXT PRIMARY KEY,
        columns_json TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_emp_org_id ON employees (organization_id, id)",
    """
    CREATE INDEX IF NOT EXISTS idx_emp_org_filters
    ON employees (organization_id, department, location, position)
    """,
    "CREATE INDEX IF NOT EXISTS idx_emp_org_name ON employees (organization_id, name)",
]


def get_connection(db_path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def get_db(request: Request) -> Iterator[sqlite3.Connection]:
    db_path = getattr(request.app.state, "db_path", None)
    if not db_path:
        raise RuntimeError("Database path is not initialized")

    connection = get_connection(db_path)
    try:
        yield connection
    finally:
        connection.close()


def init_db(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        for statement in SCHEMA_STATEMENTS:
            cursor.execute(statement)
        connection.commit()
    finally:
        connection.close()
