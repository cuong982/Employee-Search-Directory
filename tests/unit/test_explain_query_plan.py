import logging
import sqlite3

import pytest

from app.db.seed import seed_data_if_empty
from app.db.sqlite import init_db
from app.core.logging_config import configure_app_logging
from app.models.schemas import SearchFilters
from app.repositories.employee_repository import EmployeeRepository


@pytest.fixture
def db_with_indexes(tmp_path):
    db_path = str(tmp_path / "with_index.db")
    init_db(db_path)
    seed_data_if_empty(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def db_without_indexes(tmp_path):
    db_path = str(tmp_path / "no_index.db")
    # Init schema but drop all indexes immediately after
    init_db(db_path)
    seed_data_if_empty(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("DROP INDEX IF EXISTS idx_emp_org_id")
    conn.execute("DROP INDEX IF EXISTS idx_emp_org_filters")
    conn.execute("DROP INDEX IF EXISTS idx_emp_org_name")
    conn.commit()
    yield conn
    conn.close()


def _get_query_plan(connection: sqlite3.Connection, org_id: str, department: str | None = None) -> str:
    repo = EmployeeRepository()
    filters = SearchFilters(department=department)

    # Build the same query as repo.search() so we can EXPLAIN it directly
    query = (
        "SELECT id, name, email, department, location, position FROM employees\n"
        "WHERE organization_id = :organization_id"
    )
    params: dict = {"organization_id": org_id, "limit": 21}
    if department:
        query += "\nAND department = :department"
        params["department"] = department
    query += "\nORDER BY id ASC\nLIMIT :limit"

    cursor = connection.cursor()
    cursor.execute(f"EXPLAIN QUERY PLAN {query}", params)
    rows = cursor.fetchall()
    return " ".join(row["detail"] for row in rows)


def test_query_plan_uses_index_when_indexes_exist(db_with_indexes):
    plan = _get_query_plan(db_with_indexes, "org_1", department="Engineering")
    assert "SCAN" not in plan, f"Expected index usage but got full scan: {plan}"
    assert "SEARCH" in plan or "INDEX" in plan, f"Expected SEARCH/INDEX in plan: {plan}"


def test_query_plan_falls_back_to_scan_without_indexes(db_without_indexes):
    plan = _get_query_plan(db_without_indexes, "org_1", department="Engineering")
    assert "SCAN" in plan, f"Expected full table scan but got: {plan}"


class _ListHandler(logging.Handler):
    """Capture log records into a list for assertion."""

    def __init__(self):
        super().__init__()
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(self.format(record))


def test_explain_logging_emits_debug_line(db_with_indexes):
    configure_app_logging("DEBUG")

    handler = _ListHandler()
    app_logger = logging.getLogger("app")
    app_logger.addHandler(handler)
    try:
        EmployeeRepository().search(
            connection=db_with_indexes,
            organization_id="org_1",
            filters=SearchFilters(department="Engineering"),
            projected_columns=["name", "email", "department"],
            page_size=10,
            cursor=None,
        )
    finally:
        app_logger.removeHandler(handler)

    assert any("EXPLAIN QUERY PLAN" in m for m in handler.messages), (
        f"Expected EXPLAIN QUERY PLAN in log. Got: {handler.messages}"
    )
    assert any("org_1" in m for m in handler.messages)


def test_explain_logging_not_emitted_at_info_level(db_with_indexes):
    configure_app_logging("INFO")

    handler = _ListHandler()
    app_logger = logging.getLogger("app")
    app_logger.addHandler(handler)
    try:
        EmployeeRepository().search(
            connection=db_with_indexes,
            organization_id="org_1",
            filters=SearchFilters(),
            projected_columns=["name"],
            page_size=10,
            cursor=None,
        )
    finally:
        app_logger.removeHandler(handler)

    assert not any("EXPLAIN QUERY PLAN" in m for m in handler.messages), (
        f"EXPLAIN QUERY PLAN should not appear at INFO level. Got: {handler.messages}"
    )
