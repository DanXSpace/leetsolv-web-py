"""Tests for serving the built frontend (SPA) from the API origin."""

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _make_dist(tmp_path):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><html><body>app</body></html>", encoding="utf-8")
    (dist / "assets" / "app.js").write_text("console.log('app')", encoding="utf-8")
    return dist


def _client(tmp_path, dist_dir=""):
    cfg = Settings()
    cfg.dist_dir = dist_dir
    app = create_app(cfg, init_db_=False)
    return TestClient(app)


def test_spa_serves_index_for_root(tmp_path):
    client = _client(tmp_path, str(_make_dist(tmp_path)))
    resp = client.get("/")
    assert resp.status_code == 200
    assert "app" in resp.text


def test_spa_serves_index_for_deep_link(tmp_path):
    client = _client(tmp_path, str(_make_dist(tmp_path)))
    resp = client.get("/share/some-token")
    assert resp.status_code == 200
    assert "app" in resp.text


def test_spa_serves_assets(tmp_path):
    client = _client(tmp_path, str(_make_dist(tmp_path)))
    resp = client.get("/assets/app.js")
    assert resp.status_code == 200
    assert resp.text == "console.log('app')"


def test_api_still_works_with_spa_mounted(tmp_path):
    client = _client(tmp_path, str(_make_dist(tmp_path)))
    assert client.get("/api/health").json() == {"ok": True}


def test_unknown_api_route_is_404_not_index(tmp_path):
    client = _client(tmp_path, str(_make_dist(tmp_path)))
    assert client.get("/api/does-not-exist").status_code == 404


def test_no_spa_when_dist_dir_unset(tmp_path):
    client = _client(tmp_path, "")
    assert client.get("/").status_code == 404
