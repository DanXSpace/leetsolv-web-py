"""End-to-end tests for the FastAPI layer (via TestClient)."""

from datetime import date, datetime
from types import SimpleNamespace

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import create_session_token, new_share_token
from app.config import Settings
from app.db import Base
from app.deps import get_db, get_service
from app.main import create_app
from app.models import Problem
from app.scheduler import Scheduler
from app.service import QuestionService, set_setting_value

TODAY = date(2026, 10, 11)
ADD_BODY = {
    "url": "https://leetcode.com/problems/two-sum",
    "note": "use hashmap",
    "familiarity": 1,  # Hard
    "importance": 2,  # High
    "memory": 0,
}


@pytest.fixture
def api():
    # StaticPool shares one connection across the TestClient's portal thread
    # and the test thread, so the in-memory DB persists across requests.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionFactory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        with SessionFactory() as s:
            yield s

    def override_get_service(db=Depends(get_db)):
        return QuestionService(
            db,
            Scheduler(randomize_interval=False),
            today=lambda: TODAY,
            now=lambda: datetime(2026, 10, 11, 9, 0, 0),
        )

    cfg = Settings()
    cfg.secret_key = "test-secret"
    cfg.owner_github_id = "12345"
    cfg.github_client_id = "client-id"
    cfg.github_client_secret = "client-secret"
    cfg.base_url = "http://testserver"
    cfg.cors_origins = ["*"]

    app = create_app(cfg, init_db_=False)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_service] = override_get_service

    with TestClient(app) as client:
        yield SimpleNamespace(client=client, session_factory=SessionFactory, cfg=cfg)


def login_owner(api):
    api.client.cookies.set("leetsolv_session", create_session_token("12345", "dholun", "test-secret"))


def _seed(api, url, slug, next_review):
    with api.session_factory() as s:
        s.add(
            Problem(
                url=url,
                slug=slug,
                note="",
                familiarity=1,
                importance=2,
                last_reviewed=date(2026, 10, 1),
                next_review=next_review,
                review_count=1,
                ease_factor=1.8,
                created_at=datetime(2026, 10, 1, 9, 0, 0),
                updated_at=datetime(2026, 10, 1, 9, 0, 0),
            )
        )
        s.commit()


# --- health / auth boundaries ---


def test_health(api):
    assert api.client.get("/api/health").json() == {"ok": True}


def test_anonymous_blocked_from_read(api):
    assert api.client.get("/api/problems").status_code == 401
    assert api.client.get("/api/status").status_code == 401


def test_me(api):
    assert api.client.get("/api/auth/me").json()["role"] == "anonymous"
    login_owner(api)
    assert api.client.get("/api/auth/me").json()["role"] == "owner"


# --- CRUD ---


def test_add_and_list(api):
    login_owner(api)
    resp = api.client.post("/api/problems", json=ADD_BODY)
    assert resp.status_code == 201
    data = resp.json()
    assert data["slug"] == "two-sum"
    assert data["ease_factor"] == 1.8
    assert data["review_count"] == 1
    assert data["next_review"] == "2026-10-16"

    listing = api.client.get("/api/problems").json()
    assert len(listing) == 1
    assert listing[0]["id"] == data["id"]


def test_add_rejects_bad_url(api):
    login_owner(api)
    body = dict(ADD_BODY, url="https://example.com/problems/two-sum")
    assert api.client.post("/api/problems", json=body).status_code == 400


def test_review(api):
    login_owner(api)
    created = api.client.post("/api/problems", json=ADD_BODY).json()
    resp = api.client.post(
        "/api/review",
        json={"target": str(created["id"]), "familiarity": 2, "importance": 2, "memory": 0},
    )
    assert resp.status_code == 200
    assert resp.json()["review_count"] == 2
    assert resp.json()["note"] == "use hashmap"  # preserved
    assert resp.json()["familiarity"] == 2


def test_edit_note_does_not_reschedule(api):
    login_owner(api)
    created = api.client.post("/api/problems", json=ADD_BODY).json()
    resp = api.client.patch(f"/api/problems/{created['id']}/note", json={"note": "better note"})
    assert resp.status_code == 200
    assert resp.json()["note"] == "better note"
    assert resp.json()["review_count"] == 1  # unchanged
    assert resp.json()["next_review"] == "2026-10-16"  # unchanged


def test_delete_and_undo(api):
    login_owner(api)
    created = api.client.post("/api/problems", json=ADD_BODY).json()
    assert api.client.delete(f"/api/problems/{created['id']}").status_code == 204
    assert api.client.get("/api/problems").json() == []
    assert api.client.post("/api/undo").status_code == 204
    restored = api.client.get(f"/api/problems/{created['id']}").json()
    assert restored["slug"] == "two-sum"


def test_history(api):
    login_owner(api)
    api.client.post("/api/problems", json=ADD_BODY)
    h = api.client.get("/api/history").json()
    assert len(h) == 1
    assert h[0]["action"] == "add"


# --- status / search / settings ---


def test_status_buckets(api):
    login_owner(api)
    _seed(api, "https://leetcode.com/problems/a/", "a", date(2026, 10, 10))  # due
    _seed(api, "https://leetcode.com/problems/b/", "b", date(2026, 10, 11))  # due (today)
    _seed(api, "https://leetcode.com/problems/c/", "c", date(2026, 10, 12))  # upcoming
    _seed(api, "https://leetcode.com/problems/d/", "d", date(2026, 10, 20))  # future
    resp = api.client.get("/api/status").json()
    assert resp["total"] == 4
    assert resp["total_due"] == 2
    assert resp["total_upcoming"] == 1
    assert {p["slug"] for p in resp["due"]} == {"a", "b"}


def test_search(api):
    login_owner(api)
    _seed(api, "https://leetcode.com/problems/two-sum/", "two-sum", date(2026, 10, 11))
    _seed(api, "https://leetcode.com/problems/valid-palindrome/", "valid-palindrome", date(2026, 10, 11))
    resp = api.client.get("/api/search", params={"query": "two"}).json()
    assert [p["slug"] for p in resp] == ["two-sum"]


def test_settings_get_and_update(api):
    login_owner(api)
    assert api.client.get("/api/settings").json()["overdue_limit"] == 7
    updated = api.client.put("/api/settings", json={"overdue_limit": 14}).json()
    assert updated["overdue_limit"] == 14


# --- mentor share link ---


def test_share_endpoint_owner(api):
    login_owner(api)
    resp = api.client.get("/api/auth/share")
    assert resp.status_code == 200
    assert resp.json()["token"]
    assert "/share/" in resp.json()["url"]


def test_share_reset_regenerates(api):
    login_owner(api)
    t1 = api.client.get("/api/auth/share").json()["token"]
    t2 = api.client.post("/api/auth/share/reset").json()["token"]
    assert t1 != t2


def test_mentor_read_only(api):
    token = new_share_token()
    with api.session_factory() as s:
        set_setting_value(s, "share_token", token)
    # no owner cookie: mentor access via share token
    assert api.client.get("/api/status", params={"share": token}).status_code == 200
    assert api.client.get("/api/problems", params={"share": token}).status_code == 200
    assert api.client.post("/api/problems", json=ADD_BODY, params={"share": token}).status_code == 403


def test_mentor_wrong_token_rejected(api):
    assert api.client.get("/api/status", params={"share": "wrong"}).status_code == 401


# --- OAuth callback ---


def test_oauth_callback_owner(api, monkeypatch):
    async def fake_exchange(client_id, client_secret, code):
        return {"github_id": "12345", "login": "dholun"}

    monkeypatch.setattr("app.routers.auth.exchange_code", fake_exchange)
    resp = api.client.get("/api/auth/callback", params={"code": "x"}, follow_redirects=False)
    assert resp.status_code == 302
    assert api.client.get("/api/auth/me").json()["role"] == "owner"


def test_oauth_callback_rejects_non_owner(api, monkeypatch):
    async def fake_exchange(client_id, client_secret, code):
        return {"github_id": "99999", "login": "intruder"}

    monkeypatch.setattr("app.routers.auth.exchange_code", fake_exchange)
    resp = api.client.get("/api/auth/callback", params={"code": "x"})
    assert resp.status_code == 403
