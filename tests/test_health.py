"""Tests for health endpoint."""

from __future__ import annotations

from starlette.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    """Health returns 200 and non-sensitive fields."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["jira_mode"] in ("live", "mock")
    assert "model_name" in data
    assert "version" in data
    body = str(data).lower()
    assert "token" not in body
    assert "api_token" not in body
