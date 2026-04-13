"""Pytest fixtures."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    """HTTP client against a fresh app instance."""
    return TestClient(create_app())
