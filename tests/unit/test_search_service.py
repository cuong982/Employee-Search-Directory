import pytest

from app.db.seed import seed_data_if_empty
from app.db.sqlite import init_db
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
        employee_repository=EmployeeRepository(db_path),
        config_repository=ColumnConfigRepository(db_path),
    )
    return service


def test_search_service_applies_org_columns_and_hides_phone(search_service: SearchService) -> None:
    response = search_service.search(
        "org_1",
        EmployeeSearchRequest(page_size=10),
    )

    assert response.applied_columns == [
        "name",
        "email",
        "department",
        "location",
        "position",
    ]
    assert response.meta.count > 0
    for item in response.items:
        assert set(item.keys()) == set(response.applied_columns)
        assert "phone" not in item


def test_search_service_rejects_invalid_cursor(search_service: SearchService) -> None:
    with pytest.raises(ValueError, match="cursor must be a positive integer"):
        search_service.search(
            "org_1",
            EmployeeSearchRequest(page_size=10, cursor="not-a-number"),
        )
