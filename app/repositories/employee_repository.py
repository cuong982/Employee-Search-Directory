import sqlite3

from app.core.settings import ALLOWED_OUTPUT_FIELDS
from app.models.schemas import SearchFilters


class EmployeeRepository:
    def search(
        self,
        connection: sqlite3.Connection,
        organization_id: str,
        filters: SearchFilters,
        projected_columns: list[str],
        page_size: int,
        cursor: int | None,
    ) -> tuple[list[dict[str, object]], str | None]:
        safe_columns = [
            column for column in projected_columns if column in ALLOWED_OUTPUT_FIELDS
        ]
        if not safe_columns:
            safe_columns = ["name"]

        select_columns = ["id"] + [column for column in safe_columns if column != "id"]

        query_parts = [
            f"SELECT {', '.join(select_columns)} FROM employees",
            "WHERE organization_id = :organization_id",
        ]
        params: dict[str, object] = {
            "organization_id": organization_id,
            "limit": page_size + 1,
        }

        if filters.q:
            query_parts.append("AND (name LIKE :keyword OR email LIKE :keyword)")
            params["keyword"] = f"%{filters.q}%"
        if filters.department:
            query_parts.append("AND department = :department")
            params["department"] = filters.department
        if filters.location:
            query_parts.append("AND location = :location")
            params["location"] = filters.location
        if filters.position:
            query_parts.append("AND position = :position")
            params["position"] = filters.position
        if cursor is not None:
            query_parts.append("AND id > :cursor")
            params["cursor"] = cursor

        query_parts.append("ORDER BY id ASC")
        query_parts.append("LIMIT :limit")

        query = "\n".join(query_parts)

        db_cursor = connection.cursor()
        db_cursor.execute(query, params)
        rows = db_cursor.fetchall()

        has_next = len(rows) > page_size
        if has_next:
            rows = rows[:page_size]

        items: list[dict[str, object]] = []
        for row in rows:
            item: dict[str, object] = {}
            for column in safe_columns:
                item[column] = row[column]
            items.append(item)

        next_cursor = str(rows[-1]["id"]) if has_next and rows else None
        return items, next_cursor
