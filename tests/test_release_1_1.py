"""Release 1.1 hardening tests."""

from fastapi.testclient import TestClient

from app.security import rate_limit
from tests.conftest import API_KEY


def _reset_limiters():
    rate_limit.track_limiter._windows.clear()
    rate_limit.push_subscribe_limiter._windows.clear()


def test_health_includes_database_and_version(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"
    assert data["version"] == "1.1.0"
    assert "time" in data


def test_track_stores_event(client: TestClient):
    _reset_limiters()
    response = client.post(
        "/api/track",
        json={
            "project_key": "demo",
            "event_type": "pageview",
            "path": "/test",
            "visitor_id": "vis_1",
            "session_id": "sess_1",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True, "ignored": None}


def test_track_rejects_oversized_path(client: TestClient):
    _reset_limiters()
    response = client.post(
        "/api/track",
        json={
            "project_key": "demo",
            "event_type": "pageview",
            "path": "x" * 3000,
        },
    )
    assert response.status_code == 422


def test_track_rejects_oversized_payload(client: TestClient):
    _reset_limiters()
    response = client.post(
        "/api/track",
        json={
            "project_key": "demo",
            "event_type": "pageview",
            "path": "/",
            "payload": {"data": "x" * 25000},
        },
    )
    assert response.status_code == 422


def test_track_ignores_bots(client: TestClient):
    _reset_limiters()
    response = client.post(
        "/api/track",
        headers={"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1)"},
        json={
            "project_key": "demo",
            "event_type": "pageview",
            "path": "/bot-page",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True, "ignored": "bot"}


def test_track_rate_limit(client: TestClient):
    _reset_limiters()
    payload = {
        "project_key": "demo",
        "event_type": "pageview",
        "path": "/spam",
    }
    for _ in range(120):
        assert client.post("/api/track", json=payload).status_code == 200

    blocked = client.post("/api/track", json=payload)
    assert blocked.status_code == 429
    assert blocked.json() == {"detail": "Rate limit exceeded"}


def test_push_subscribe_rate_limit(client: TestClient):
    _reset_limiters()
    for i in range(20):
        response = client.post(
            "/api/push/subscribe",
            json={
                "project_key": "demo",
                "endpoint": f"https://push.example/sub/{i}",
                "keys": {"p256dh": "k", "auth": "a"},
            },
        )
        assert response.status_code == 200

    blocked = client.post(
        "/api/push/subscribe",
        json={
            "project_key": "demo",
            "endpoint": "https://push.example/sub/extra",
            "keys": {"p256dh": "k", "auth": "a"},
        },
    )
    assert blocked.status_code == 429
    assert blocked.json() == {"detail": "Rate limit exceeded"}


def test_stats_requires_api_key(client: TestClient):
    response = client.get("/api/stats/demo")
    assert response.status_code == 401


def test_stats_rejects_invalid_api_key(client: TestClient):
    response = client.get("/api/stats/demo", headers={"X-API-Key": "wrong"})
    assert response.status_code == 403


def test_stats_with_valid_api_key(client: TestClient):
    response = client.get("/api/stats/demo", headers={"X-API-Key": API_KEY})
    assert response.status_code == 200
    assert response.json()["project_key"] == "demo"


def test_dashboard_renders_without_unsafe_html(client: TestClient):
    _reset_limiters()
    client.post(
        "/api/track",
        json={
            "project_key": "demo",
            "event_type": "pageview",
            "path": "/<script>alert(1)</script>",
            "title": "<img onerror=alert(1)>",
            "referrer": "javascript:alert(1)",
        },
    )
    response = client.get("/dashboard/demo", headers={"X-API-Key": API_KEY})
    assert response.status_code == 200
    body = response.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in body
    assert "&lt;img onerror=alert(1)&gt;" in body
    assert "javascript:alert(1)" in body
    assert "<script>alert(1)</script>" not in body
