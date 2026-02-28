from fastapi import FastAPI

from app.api.search import router as search_router
from app.core.rate_limiter import FixedWindowRateLimiter
from app.core.settings import (
    API_DESCRIPTION,
    API_TITLE,
    API_VERSION,
    DEFAULT_RATE_LIMIT,
    DEFAULT_RATE_WINDOW_SECONDS,
    resolve_db_path,
)
from app.db.seed import seed_data_if_empty
from app.db.sqlite import init_db
from app.repositories.config_repository import ColumnConfigRepository
from app.repositories.employee_repository import EmployeeRepository
from app.services.search_service import SearchService


def create_app(
    db_path: str | None = None,
    seed: bool = True,
    rate_limit: int = DEFAULT_RATE_LIMIT,
    rate_window_seconds: int = DEFAULT_RATE_WINDOW_SECONDS,
) -> FastAPI:
    app = FastAPI(
        title=API_TITLE,
        version=API_VERSION,
        description=API_DESCRIPTION,
    )

    resolved_db_path = resolve_db_path(db_path)
    init_db(resolved_db_path)
    if seed:
        seed_data_if_empty(resolved_db_path)

    employee_repository = EmployeeRepository(resolved_db_path)
    config_repository = ColumnConfigRepository(resolved_db_path)

    app.state.search_service = SearchService(employee_repository, config_repository)
    app.state.rate_limiter = FixedWindowRateLimiter(
        limit=rate_limit,
        window_seconds=rate_window_seconds,
    )

    app.include_router(search_router)

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
