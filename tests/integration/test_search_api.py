from fastapi.testclient import TestClient

from app.main import create_app


def _build_client(tmp_path, rate_limit: int = 60) -> TestClient:
    app = create_app(
        db_path=str(tmp_path / "integration.db"),
        seed=True,
        rate_limit=rate_limit,
        rate_window_seconds=60,
    )
    return TestClient(app)


def test_missing_org_header_returns_422(tmp_path) -> None:
    with _build_client(tmp_path) as client:
        response = client.get("/api/v1/employees/search")
        assert response.status_code == 422


def test_whitespace_org_header_returns_400(tmp_path) -> None:
    with _build_client(tmp_path) as client:
        response = client.get(
            "/api/v1/employees/search",
            headers={"X-Org-Id": "   "},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "X-Org-Id header is required"


def test_tenant_isolation_for_keyword_search(tmp_path) -> None:
    with _build_client(tmp_path) as client:
        response = client.get(
            "/api/v1/employees/search",
            headers={"X-Org-Id": "org_1"},
            params={"q": "David"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["items"] == []


def test_filter_combination_and_projection(tmp_path) -> None:
    with _build_client(tmp_path) as client:
        response = client.get(
            "/api/v1/employees/search",
            headers={"X-Org-Id": "org_1"},
            params={"department": "Engineering", "location": "HCM", "page_size": 10},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["meta"]["count"] == 2

        for item in payload["items"]:
            assert item["department"] == "Engineering"
            assert item["location"] == "HCM"
            assert "phone" not in item


def test_dynamic_columns_differ_between_organizations(tmp_path) -> None:
    with _build_client(tmp_path) as client:
        response_org_1 = client.get(
            "/api/v1/employees/search",
            headers={"X-Org-Id": "org_1"},
        )
        response_org_2 = client.get(
            "/api/v1/employees/search",
            headers={"X-Org-Id": "org_2"},
        )

        assert response_org_1.status_code == 200
        assert response_org_2.status_code == 200

        org_1_payload = response_org_1.json()
        org_2_payload = response_org_2.json()

        assert "email" in org_1_payload["applied_columns"]
        assert "email" not in org_2_payload["applied_columns"]

        assert set(org_1_payload["items"][0].keys()) == set(
            org_1_payload["applied_columns"]
        )
        assert set(org_2_payload["items"][0].keys()) == set(
            org_2_payload["applied_columns"]
        )


def test_cursor_pagination_returns_next_cursor(tmp_path) -> None:
    with _build_client(tmp_path) as client:
        first_page = client.get(
            "/api/v1/employees/search",
            headers={"X-Org-Id": "org_1"},
            params={"page_size": 1},
        )

        assert first_page.status_code == 200
        first_payload = first_page.json()
        assert first_payload["meta"]["count"] == 1
        assert first_payload["next_cursor"] is not None

        second_page = client.get(
            "/api/v1/employees/search",
            headers={"X-Org-Id": "org_1"},
            params={"page_size": 1, "cursor": first_payload["next_cursor"]},
        )

        assert second_page.status_code == 200
        second_payload = second_page.json()
        assert second_payload["meta"]["count"] == 1
        assert second_payload["items"][0] != first_payload["items"][0]


def test_rate_limit_returns_429(tmp_path) -> None:
    with _build_client(tmp_path, rate_limit=2) as client:
        headers = {"X-Org-Id": "org_1", "X-User-Id": "user_1"}

        response_1 = client.get("/api/v1/employees/search", headers=headers)
        response_2 = client.get("/api/v1/employees/search", headers=headers)
        response_3 = client.get("/api/v1/employees/search", headers=headers)

        assert response_1.status_code == 200
        assert response_2.status_code == 200
        assert response_3.status_code == 429
        assert "Retry-After" in response_3.headers


def test_rate_limit_ignores_spoofed_forwarded_for(tmp_path) -> None:
    with _build_client(tmp_path, rate_limit=2) as client:
        base_headers = {"X-Org-Id": "org_1", "X-User-Id": "spoof_user"}

        response_1 = client.get(
            "/api/v1/employees/search",
            headers={**base_headers, "X-Forwarded-For": "1.1.1.1"},
        )
        response_2 = client.get(
            "/api/v1/employees/search",
            headers={**base_headers, "X-Forwarded-For": "8.8.8.8"},
        )
        response_3 = client.get(
            "/api/v1/employees/search",
            headers={**base_headers, "X-Forwarded-For": "9.9.9.9"},
        )

        assert response_1.status_code == 200
        assert response_2.status_code == 200
        assert response_3.status_code == 429


def test_openapi_endpoint_is_available(tmp_path) -> None:
    with _build_client(tmp_path) as client:
        response = client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()
        assert "/api/v1/employees/search" in schema["paths"]
        parameters = schema["paths"]["/api/v1/employees/search"]["get"]["parameters"]
        org_header = [p for p in parameters if p["name"] == "X-Org-Id"][0]
        assert org_header["required"] is True
        assert not any(p["name"] == "X-Forwarded-For" for p in parameters)
        items_schema = schema["components"]["schemas"]["SearchResponse"]["properties"][
            "items"
        ]["items"]
        assert items_schema["$ref"] == "#/components/schemas/EmployeeItem"
