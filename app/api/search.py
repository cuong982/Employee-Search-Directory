import sqlite3

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request

from app.db.sqlite import get_db
from app.models.schemas import EmployeeSearchRequest, SearchResponse

router = APIRouter(prefix="/api/v1/employees", tags=["employee-search"])


def get_org_id(x_org_id: str = Header(..., alias="X-Org-Id")) -> str:
    normalized_org_id = x_org_id.strip()
    if not normalized_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id header is required")
    return normalized_org_id


@router.get(
    "/search",
    response_model=SearchResponse,
    response_model_exclude_none=True,
)
def search_employees(
    request: Request,
    db: sqlite3.Connection = Depends(get_db),
    org_id: str = Depends(get_org_id),
    q: str | None = Query(default=None),
    department: str | None = Query(default=None),
    location: str | None = Query(default=None),
    position: str | None = Query(default=None),
    page_size: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> SearchResponse:
    client_ip = request.client.host if request.client and request.client.host else "unknown"
    user_id = x_user_id or "anon"

    limiter = request.app.state.rate_limiter
    key = f"{org_id}:{user_id}:{client_ip}"
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
        return service.search(org_id, payload, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
