from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_invalid_timezone_is_not_a_success():
    response = client.get("/api/world-clock/Not/A_Zone")
    assert response.status_code == 404


def test_hyphenated_timezone_is_preserved():
    response = client.get("/api/world-clock/America/Port-au-Prince")
    assert response.status_code == 200
    assert response.json()["timezone"] == "America/Port-au-Prince"


def test_timezone_search_accepts_spaces_and_nested_cities():
    response = client.get("/api/timezones", params={"q": "buenos aires"})
    assert response.status_code == 200
    assert "America/Argentina/Buenos_Aires" in response.json()["zones"]
    assert all("Buenos_Aires" in zone for zone in response.json()["zones"])


def test_default_page_is_bounded():
    response = client.get("/api/timezones")
    assert response.status_code == 200
    assert len(response.json()["zones"]) == 12


def test_pagination_is_disjoint_and_accepts_explicit_page_sizes():
    for size in (12, 24, 48):
        first = client.get("/api/timezones", params={"page_size": size}).json()
        second = client.get("/api/timezones", params={"page_size": size, "page": 2}).json()
        assert len(first["zones"]) == size
        assert len(second["zones"]) == size
        assert not set(first["zones"]) & set(second["zones"])
        assert first["total"] == second["total"]
        assert first["zones"] == sorted(first["zones"])


def test_invalid_query_constraints_and_missing_page():
    for params in (
        {"q": "a" * 81},
        {"region": "Invalid"},
        {"page": 0},
        {"page_size": 13},
        {"page_size": 100000},
        {"page": "abc"},
    ):
        assert client.get("/api/timezones", params=params).status_code == 422
    assert client.get("/api/timezones?page=9999").status_code == 404


def test_region_filter_empty_result_and_last_page():
    data = client.get("/api/timezones?region=Asia&page_size=48").json()
    assert all(zone.startswith("Asia/") for zone in data["zones"])
    empty = client.get("/api/timezones?q=zzzzzzzz").json()
    assert empty["zones"] == [] and empty["total"] == 0 and empty["pages"] == 1
    data = client.get("/api/timezones").json()
    last = client.get("/api/timezones", params={"page": data["pages"]}).json()
    assert 1 <= len(last["zones"]) <= 12


def test_time_sync_is_fresh_and_timezone_includes_date_and_offset():
    import time

    response = client.get("/api/time")
    assert abs(response.json()["epoch_ms"] - time.time() * 1000) < 2000
    assert response.headers["cache-control"] == "no-store"
    data = client.get("/api/world-clock/Etc/GMT-1").json()
    assert data["iso"].endswith("+01:00")
    assert data["date"] in data["iso"]


def test_home_assets_health_and_security_headers_work_outside_repo(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for path in (
        "/",
        "/static/js/core.mjs",
        "/static/js/main.js",
        "/static/css/style.css",
        "/health",
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert response.headers["x-content-type-options"] == "nosniff"
        assert "script-src 'self'" in response.headers["content-security-policy"]
    assert "javascript" in client.get("/static/js/core.mjs").headers["content-type"]
    assert client.get("/health").json() == {"status": "ok"}
