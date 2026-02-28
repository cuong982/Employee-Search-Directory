# Employee Search Service (FastAPI)

## 1. Problem framing
This project implements a **search-only** employee directory API for a multi-tenant HR context.

The assignment priorities are:
- strict assignment scope (no CRUD APIs),
- tenant-safe data access,
- dynamic output columns by organization,
- custom in-house rate limiting,
- containerized delivery with OpenAPI and tests.

## 2. Scope and assumptions
### In scope
- `GET /api/v1/employees/search`
- org-level configurable output columns
- custom fixed-window rate limiter (in-memory)
- SQLite runtime with indexed query patterns
- unit and integration tests

### Out of scope
- employee CRUD APIs
- organization config CRUD APIs
- real authentication (header-based org/user identity only)

### Assumption for dependency rule
The assignment says FastAPI is mandatory while also saying standard library only.
This submission interprets that as:
- runtime framework: FastAPI + Uvicorn,
- no external library for rate limiting (custom implementation),
- tests may use external testing tools.

## 3. Architecture decisions
- Layered architecture: API -> Service -> Repository -> SQLite.
- Request-scoped DB connection via FastAPI dependency (open per request, close in `finally`).
- Repository always enforces `organization_id` predicate.
- Response projection is built from `allowed_fields ∩ org_config`.
- Keyset pagination uses `id > cursor` and `ORDER BY id ASC`.
- Search endpoint remains sync (`def`) because `sqlite3` is sync I/O.

See [ARCHITECTURE.md](./ARCHITECTURE.md) for details.

## 4. API contract
### Endpoint
`GET /api/v1/employees/search`

### Required header
- `X-Org-Id`

### Optional headers
- `X-User-Id`

### Query params
- `q` (keyword on name/email)
- `department`
- `location`
- `position`
- `page_size` (default `20`, max `100`)
- `cursor` (keyset cursor)

### Response shape
```json
{
  "items": [{"name": "...", "department": "..."}],
  "next_cursor": "2",
  "applied_columns": ["name", "department", "position"],
  "meta": {
    "page_size": 20,
    "count": 1
  }
}
```

## 5. Data-leak safeguards
- No `SELECT *` queries.
- Every search query includes `WHERE organization_id = :organization_id`.
- UI payload is restricted to configured columns per organization.
- Non-configured attributes (including `phone` if not configured) are never returned.

## 6. Performance choices
- Index-first filtering with mandatory org predicate.
- Keyset pagination (`id > cursor`) for large datasets.
- Projection-only reads to reduce payload and data exposure.

## 7. Rate limiter design
- Algorithm: fixed-window counter.
- Key format: `{org_id}:{user_id_or_anon}:{client_ip}`.
- Default policy: `60 requests / 60 seconds`.
- Thread-safe via `threading.Lock`.
- Memory safeguards:
  - periodic cleanup of expired keys,
  - `max_tracked_keys` cap to prevent unbounded growth under key-cardinality abuse.

Limitation:
- Per-process memory only (not distributed across replicas).

## 8. Runtime configuration (env vars)
- `APP_DB_PATH`: SQLite file path (default: `data/app.db`).
- `APP_SEED_DATA`: seed sample data on startup (`true`/`false`, default: `true`).
- `RATE_LIMIT_MAX_TRACKED_KEYS`: max in-memory key entries (default: `200000`).
- `RATE_LIMIT_CLEANUP_INTERVAL_SECONDS`: cleanup interval for expired keys (default: `30`).

OpenAPI note:
- `items` is documented as a typed `EmployeeItem` model with optional fields.
- Response uses `response_model_exclude_none=True`, so only configured columns are returned.

## 9. Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

OpenAPI docs:
- [http://localhost:8000/docs](http://localhost:8000/docs)
- [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

## 10. Run with Docker
```bash
docker compose up --build
```

## 11. Run tests
```bash
pip install -r requirements-dev.txt
pytest -q
```

## 12. Sample curl
```bash
curl -s 'http://localhost:8000/api/v1/employees/search?page_size=2' \
  -H 'X-Org-Id: org_1' \
  -H 'X-User-Id: reviewer_1'
```

## 13. Production migration notes (not implemented)
- Replace SQLite with PostgreSQL.
- Move rate limiting to Redis for distributed consistency.
- Add observability (structured logs, metrics, traces).
- Use signed/encoded cursors (for example, base64 payload + HMAC signature) to prevent cursor tampering and hide internal pagination details.
