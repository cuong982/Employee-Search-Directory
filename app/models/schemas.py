from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.core.settings import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class SearchFilters(BaseModel):
    q: str | None = None
    department: str | None = None
    location: str | None = None
    position: str | None = None

    @field_validator("q", "department", "location", "position", mode="before")
    @classmethod
    def empty_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class EmployeeSearchRequest(SearchFilters):
    page_size: int = Field(default=DEFAULT_PAGE_SIZE)
    cursor: str | None = None

    @field_validator("page_size")
    @classmethod
    def validate_page_size(cls, value: int) -> int:
        if value < 1 or value > MAX_PAGE_SIZE:
            raise ValueError(f"page_size must be between 1 and {MAX_PAGE_SIZE}")
        return value


class SearchMeta(BaseModel):
    page_size: int
    count: int


class SearchResponse(BaseModel):
    items: list[dict[str, Any]]
    next_cursor: str | None
    applied_columns: list[str]
    meta: SearchMeta
