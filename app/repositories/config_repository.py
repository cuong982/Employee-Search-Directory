import json

from app.core.settings import DEFAULT_VISIBLE_COLUMNS
from app.db.sqlite import get_connection


class ColumnConfigRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_columns_for_org(self, organization_id: str) -> list[str]:
        connection = get_connection(self.db_path)
        try:
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
        finally:
            connection.close()
