import pytest

from app.db.seed import seed_data_if_empty
from app.db.sqlite import get_connection, init_db
from app.models.schemas import EmployeeSearchRequest
from app.repositories.config_repository import ColumnConfigRepository
from app.repositories.employee_repository import EmployeeRepository
from app.services.search_service import SearchService


@pytest.fixture
def search_service(tmp_path):
    db_path = str(tmp_path / "unit.db")
    init_db(db_path)
    seed_data_if_empty(db_path)

    service = SearchService(
        employee_repository=EmployeeRepository(),
        config_repository=ColumnConfigRepository(),
    )
    return service, db_path


def test_search_service_applies_org_columns_and_hides_phone(search_service: SearchService) -> None:
    service, db_path = search_service
    connection = get_connection(db_path)
    try:
        response = service.search(
            "org_1",
            EmployeeSearchRequest(page_size=10),
            connection,
        )
    finally:
        connection.close()

    assert response.applied_columns == [
        "name",
        "email",
        "department",
        "location",
        "position",
    ]
    assert response.meta.count > 0
    for item in response.items:
        projected = item.model_dump(exclude_none=True)
        assert set(projected.keys()) == set(response.applied_columns)
        assert "phone" not in projected


def test_search_service_rejects_invalid_cursor(search_service: SearchService) -> None:
    service, db_path = search_service
    connection = get_connection(db_path)
    try:
        with pytest.raises(ValueError, match="cursor must be a positive integer"):
            service.search(
                "org_1",
                EmployeeSearchRequest(page_size=10, cursor="not-a-number"),
                connection,
            )
    finally:
        connection.close()
