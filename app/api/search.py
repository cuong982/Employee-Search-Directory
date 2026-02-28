from fastapi import APIRouter, Header, HTTPException, Query, Request

from app.models.schemas import EmployeeSearchRequest, SearchResponse

router = APIRouter(prefix="/api/v1/employees", tags=["employee-search"])


def _extract_client_ip(x_forwarded_for: str | None, fallback: str | None) -> str:
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip() or "unknown"
    return fallback or "unknown"


@router.get("/search", response_model=SearchResponse)
def search_employees(
    request: Request,
    q: str | None = Query(default=None),
    department: str | None = Query(default=None),
    location: str | None = Query(default=None),
    position: str | None = Query(default=None),
    page_size: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    x_org_id: str = Header(..., alias="X-Org-Id"),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_forwarded_for: str | None = Header(default=None, alias="X-Forwarded-For"),
) -> SearchResponse:
    if not x_org_id.strip():
        raise HTTPException(status_code=400, detail="X-Org-Id header is required")

    client_host = request.client.host if request.client else None
    client_ip = _extract_client_ip(x_forwarded_for, client_host)
    user_id = x_user_id or "anon"

    limiter = request.app.state.rate_limiter
    key = f"{x_org_id}:{user_id}:{client_ip}"
    allowed, retry_after = limiter.allow(key)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )

    payload = EmployeeSearchRequest(
        q=q,
        department=department,
        location=location,
        position=position,
        page_size=page_size,
        cursor=cursor,
    )

    service = request.app.state.search_service
    try:
        return service.search(x_org_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
