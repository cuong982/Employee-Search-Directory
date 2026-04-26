from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.search import router as search_router
from app.core.logging_config import configure_app_logging
from app.core.rate_limiter import FixedWindowRateLimiter
from app.core.settings import (
    APP_SEED_DATA,
    API_DESCRIPTION,
    API_TITLE,
    API_VERSION,
    DEFAULT_RATE_LIMIT,
    DEFAULT_RATE_WINDOW_SECONDS,
    LOG_LEVEL,
    RATE_LIMIT_CLEANUP_INTERVAL_SECONDS,
    RATE_LIMIT_MAX_TRACKED_KEYS,
    resolve_db_path,
)
from app.db.seed import seed_data_if_empty
from app.db.sqlite import init_db
from app.repositories.config_repository import ColumnConfigRepository
from app.repositories.employee_repository import EmployeeRepository
from app.services.search_service import SearchService


def create_app(
    db_path: str | None = None,
    seed: bool = APP_SEED_DATA,
    rate_limit: int = DEFAULT_RATE_LIMIT,
    rate_window_seconds: int = DEFAULT_RATE_WINDOW_SECONDS,
    rate_limit_max_tracked_keys: int = RATE_LIMIT_MAX_TRACKED_KEYS,
    rate_limit_cleanup_interval_seconds: int = RATE_LIMIT_CLEANUP_INTERVAL_SECONDS,
) -> FastAPI:
    resolved_db_path = resolve_db_path(db_path)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        configure_app_logging(LOG_LEVEL)

        app.state.db_path = resolved_db_path
        init_db(resolved_db_path)
        if seed:
            seed_data_if_empty(resolved_db_path)

        employee_repository = EmployeeRepository()
        config_repository = ColumnConfigRepository()

        app.state.search_service = SearchService(employee_repository, config_repository)
        app.state.rate_limiter = FixedWindowRateLimiter(
            limit=rate_limit,
            window_seconds=rate_window_seconds,
            max_tracked_keys=rate_limit_max_tracked_keys,
            cleanup_interval_seconds=rate_limit_cleanup_interval_seconds,
        )
        yield

    app = FastAPI(
        title=API_TITLE,
        version=API_VERSION,
        description=API_DESCRIPTION,
        lifespan=lifespan,
    )

    app.include_router(search_router)

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
