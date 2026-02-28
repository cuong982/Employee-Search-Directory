import sqlite3

from app.core.settings import ALLOWED_OUTPUT_FIELDS, DEFAULT_VISIBLE_COLUMNS
from app.models.schemas import EmployeeSearchRequest, SearchMeta, SearchResponse
from app.repositories.config_repository import ColumnConfigRepository
from app.repositories.employee_repository import EmployeeRepository


class SearchService:
    def __init__(
        self,
        employee_repository: EmployeeRepository,
        config_repository: ColumnConfigRepository,
    ):
        self.employee_repository = employee_repository
        self.config_repository = config_repository

    def search(
        self,
        organization_id: str,
        request: EmployeeSearchRequest,
        connection: sqlite3.Connection,
    ) -> SearchResponse:
        parsed_cursor = self._parse_cursor(request.cursor)
        configured_columns = self.config_repository.get_columns_for_org(
            connection=connection,
            organization_id=organization_id,
        )

        effective_columns = [
            column for column in configured_columns if column in ALLOWED_OUTPUT_FIELDS
        ]
        if not effective_columns:
            effective_columns = list(DEFAULT_VISIBLE_COLUMNS)

        rows, next_cursor = self.employee_repository.search(
            connection=connection,
            organization_id=organization_id,
            filters=request,
            projected_columns=effective_columns,
            page_size=request.page_size,
            cursor=parsed_cursor,
        )

        return SearchResponse(
            items=rows,
            next_cursor=next_cursor,
            applied_columns=effective_columns,
            meta=SearchMeta(page_size=request.page_size, count=len(rows)),
        )

    @staticmethod
    def _parse_cursor(cursor: str | None) -> int | None:
        if cursor is None:
            return None

        cursor = cursor.strip()
        if cursor == "":
            return None

        if not cursor.isdigit():
            raise ValueError("cursor must be a positive integer")

        value = int(cursor)
        if value < 0:
            raise ValueError("cursor must be a positive integer")

        return value
