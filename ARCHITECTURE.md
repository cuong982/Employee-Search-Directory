# Architecture Notes

## Request flow
1. API layer (`app/api/search.py`)
- validates required org header,
- applies rate limiting,
- maps HTTP input to request DTO.

2. Service layer (`app/services/search_service.py`)
- parses cursor,
- resolves organization column configuration,
- applies safe projection intersection,
- orchestrates repository search.

3. Repository layer (`app/repositories/employee_repository.py`)
- executes parameterized SQL,
- enforces tenant boundary by `organization_id`,
- performs keyset pagination and returns next cursor.

4. Database layer (`app/db/sqlite.py`)
- SQLite schema and indexes for assignment runtime.

## Why this design for strict assignment
- Keeps implementation focused on only one API.
- Prevents common data leak mistakes in multi-tenant systems.
- Makes extension predictable without introducing unnecessary abstractions.

## Security and leak prevention
- Mandatory org predicate in repository query.
- Projection whitelist from allowed fields and per-org config.
- No wildcard DB selection.

## Production improvements (not in scope)
- PostgreSQL with migration tooling.
- Redis-backed distributed rate limit.
- Observability pipeline and SLO monitoring.
- Real authn/authz (JWT, tenant claims, role-based controls).
