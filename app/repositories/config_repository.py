import json
import logging
import sqlite3

logger = logging.getLogger(__name__)


class ColumnConfigRepository:
    def get_columns_for_org(
        self, connection: sqlite3.Connection, organization_id: str
    ) -> list[str]:
        """Return configured columns for org. Returns [] if org has no config or config is invalid."""
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
            return []

        try:
            columns = json.loads(row["columns_json"])
        except json.JSONDecodeError:
            logger.warning("Invalid columns_json for org=%s", organization_id)
            return []

        if not isinstance(columns, list):
            logger.warning("columns_json is not a list for org=%s", organization_id)
            return []

        valid = [column for column in columns if isinstance(column, str)]
        if not valid:
            return []

        return valid
