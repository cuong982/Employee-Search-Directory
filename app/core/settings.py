import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = BASE_DIR / "data" / "app.db"

API_TITLE = "Employee Search Service"
API_VERSION = "1.0.0"
API_DESCRIPTION = (
    "Search-only FastAPI microservice for multi-tenant employee directory."
)

ALLOWED_OUTPUT_FIELDS = [
    "id",
    "name",
    "email",
    "department",
    "location",
    "position",
    "phone",
]
DEFAULT_VISIBLE_COLUMNS = ["name", "email", "department", "location"]

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

DEFAULT_RATE_LIMIT = 60
DEFAULT_RATE_WINDOW_SECONDS = 60
DEFAULT_RATE_LIMIT_MAX_TRACKED_KEYS = 200_000
DEFAULT_RATE_LIMIT_CLEANUP_INTERVAL_SECONDS = 30


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


APP_SEED_DATA = _env_bool("APP_SEED_DATA", True)
RATE_LIMIT_MAX_TRACKED_KEYS = max(
    1, _env_int("RATE_LIMIT_MAX_TRACKED_KEYS", DEFAULT_RATE_LIMIT_MAX_TRACKED_KEYS)
)
RATE_LIMIT_CLEANUP_INTERVAL_SECONDS = max(
    1,
    _env_int(
        "RATE_LIMIT_CLEANUP_INTERVAL_SECONDS",
        DEFAULT_RATE_LIMIT_CLEANUP_INTERVAL_SECONDS,
    ),
)


def resolve_db_path(db_path: str | None = None) -> str:
    if db_path:
        return db_path
    return os.getenv("APP_DB_PATH", str(DEFAULT_DB_PATH))
