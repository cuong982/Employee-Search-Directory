import logging
import sqlite3

from app.models.schemas import SearchFilters

logger = logging.getLogger(__name__)


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
        safe_columns = projected_columns if projected_columns else ["name"]

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
            query_parts.append(
                "AND (name LIKE :keyword ESCAPE '\\' OR email LIKE :keyword ESCAPE '\\')"
            )
            escaped = filters.q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            params["keyword"] = f"%{escaped}%"
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

        if logger.isEnabledFor(logging.DEBUG):
            db_cursor.execute(f"EXPLAIN QUERY PLAN {query}", params)
            plan_rows = db_cursor.fetchall()
            plan_lines = " | ".join(
                f"[{r['id']},{r['parent']},{r['notused']}] {r['detail']}"
                for r in plan_rows
            )
            logger.debug("EXPLAIN QUERY PLAN org=%s: %s", organization_id, plan_lines)

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
