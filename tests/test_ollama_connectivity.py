from __future__ import annotations

import httpx
import pytest

from app.agents.model_client import OllamaConnectionError, OllamaModelClient
from app.core.config import Settings


class _FakeResponse:
    def __init__(self, *, status_code: int, json_data: dict):
        self.status_code = status_code
        self._json_data = json_data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", "http://example/api/tags")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("error", request=request, response=response)

    def json(self) -> dict:
        return self._json_data


def test_ping_success(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_get(self: httpx.Client, url: str):  # noqa: ANN001
        _ = (self, url)
        return _FakeResponse(status_code=200, json_data={"models": [{"name": "qwen2.5:7b"}]})

    monkeypatch.setattr(httpx.Client, "get", _fake_get)
    client = OllamaModelClient(settings=Settings(model_name="qwen2.5:7b"))
    assert client.ping() is True


def test_ping_model_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_get(self: httpx.Client, url: str):  # noqa: ANN001
        _ = (self, url)
        return _FakeResponse(status_code=200, json_data={"models": [{"name": "llama3:8b"}]})

    monkeypatch.setattr(httpx.Client, "get", _fake_get)
    client = OllamaModelClient(settings=Settings(model_name="qwen2.5:7b"))
    with pytest.raises(OllamaConnectionError) as exc:
        client.ping()
    assert "not found" in str(exc.value).lower()


def test_ping_connect_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_get(self: httpx.Client, url: str):  # noqa: ANN001
        raise httpx.ConnectError("connect failed", request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.Client, "get", _fake_get)
    client = OllamaModelClient(settings=Settings(model_name="qwen2.5:7b"))
    with pytest.raises(OllamaConnectionError) as exc:
        client.ping()
    assert "ollama serve" in str(exc.value).lower()


def test_generate_json_connect_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_post(self: httpx.Client, url: str, json: dict):  # noqa: ANN001
        _ = (self, json)
        raise httpx.ConnectError("connect failed", request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx.Client, "post", _fake_post)
    client = OllamaModelClient(settings=Settings(model_name="qwen2.5:7b"))
    with pytest.raises(OllamaConnectionError):
        client.generate_json(
            system_prompt="sys",
            user_prompt="user",
            json_schema={"type": "object"},
        )

