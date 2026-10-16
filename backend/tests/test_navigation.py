import pytest
from fastapi.testclient import TestClient
import backend.main as main


NAVIGATION_HEADERS = {
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Dest": "document",
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    dist = tmp_path / "frontend" / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><title>Easy Street</title>", encoding="utf-8")
    monkeypatch.setattr(main, "ROOT", tmp_path)
    with TestClient(main.create_app(tmp_path / "data"), base_url="http://localhost") as client:
        yield client


@pytest.mark.parametrize("path", ["/", "/index.html"])
def test_cross_site_top_level_navigation_can_open_only_static_entry(client, path):
    response = client.get(path, headers=NAVIGATION_HEADERS)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "<title>Easy Street</title>" in response.text


@pytest.mark.parametrize("method,path,override", [
    ("GET", "/api/config", {}),
    ("GET", "/api/documents", {}),
    ("POST", "/api/documents/sample", {}),
    ("POST", "/", {}),
    ("HEAD", "/", {}),
    ("GET", "/learning-road.png", {}),
    ("GET", "/", {"Sec-Fetch-Mode": "cors"}),
    ("GET", "/", {"Sec-Fetch-Mode": ""}),
    ("GET", "/", {"Sec-Fetch-Dest": "iframe"}),
    ("GET", "/", {"Sec-Fetch-Dest": ""}),
])
def test_navigation_exception_does_not_allow_api_mutations_or_other_fetches(client, method, path, override):
    response = client.request(method, path, headers={**NAVIGATION_HEADERS, **override})
    assert response.status_code == 403


def test_foreign_origin_still_blocks_top_level_entry_navigation(client):
    response = client.get("/", headers={**NAVIGATION_HEADERS, "Origin": "https://foreign.example"})
    assert response.status_code == 403
    assert "origin" in response.json()["detail"]


def test_navigation_exception_preserves_host_validation(client):
    response = client.get("/", headers={**NAVIGATION_HEADERS, "Host": "foreign.example"})
    assert response.status_code == 400
