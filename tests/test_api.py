from fastapi.testclient import TestClient


def test_list_files_returns_200(client: TestClient):
    resp = client.get("/api/files")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    names = {f["name"] for f in data}
    assert "auth_service.py" in names
    assert "payment_service.py" in names


def test_list_files_counts_symbols(client: TestClient):
    resp = client.get("/api/files")
    data = {f["name"]: f for f in resp.json()}
    auth = data["auth_service.py"]

    assert auth["classes_count"] == 1
    assert auth["functions_count"] == 2
    assert auth["symbols_count"] == 3


def test_list_files_pagination(client: TestClient):
    resp = client.get("/api/files?limit=1&offset=0")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_list_files_invalid_limit_rejected(client: TestClient):
    resp = client.get("/api/files?limit=0")
    assert resp.status_code == 422


def test_file_structure_found(client: TestClient):
    resp = client.get("/api/files/auth_service.py/structure")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    item = data[0]
    assert item["name"] == "auth_service.py"
    assert {s["name"] for s in item["symbols"]} == {"login", "logout", "AuthService"}


def test_file_structure_not_found_returns_empty(client: TestClient):
    resp = client.get("/api/files/nothing.py/structure")
    assert resp.status_code == 200
    assert resp.json() == []


def test_file_structure_case_insensitive(client: TestClient):
    resp = client.get("/api/files/AUTH_SERVICE.PY/structure")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_search_by_name(client: TestClient):
    resp = client.get("/api/search?q=auth")
    assert resp.status_code == 200
    names = {r["name"] for r in resp.json()}
    assert "login" in names or "AuthService" in names


def test_search_by_docstring(client: TestClient):
    resp = client.get("/api/search?q=auth%20logic")
    assert resp.status_code == 200
    names = {r["name"] for r in resp.json()}
    assert "AuthService" in names


def test_search_with_type_filter(client: TestClient):
    resp = client.get("/api/search?q=serv&type=class")
    for r in resp.json():
        assert r["type"] == "class"


def test_search_no_results_returns_empty(client: TestClient):
    resp = client.get("/api/search?q=not_real_symbol_zzz")
    assert resp.status_code == 200
    assert resp.json() == []


def test_search_empty_query_rejected(client: TestClient):
    resp = client.get("/api/search")
    assert resp.status_code == 422


def test_stats_returns_correct_shape(client: TestClient):
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()

    assert data["files"] == 2
    assert data["functions"] == 3
    assert data["classes"] == 2
    assert data["symbols"] == 5
