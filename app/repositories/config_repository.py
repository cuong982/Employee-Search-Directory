import json
import sqlite3

from app.core.settings import DEFAULT_VISIBLE_COLUMNS


class ColumnConfigRepository:
    def get_columns_for_org(
        self, connection: sqlite3.Connection, organization_id: str
    ) -> list[str]:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT columns_json
            FROM organization_column_config
            WHERE organization_id = :organization_id
            LIMIT 1
            """,
            {"organization_id": organization_id},
        )
        row = cursor.fetchone()
        if not row:
            return list(DEFAULT_VISIBLE_COLUMNS)

        try:
            columns = json.loads(row["columns_json"])
        except json.JSONDecodeError:
            return list(DEFAULT_VISIBLE_COLUMNS)

        if not isinstance(columns, list):
            return list(DEFAULT_VISIBLE_COLUMNS)

        return [column for column in columns if isinstance(column, str)]
