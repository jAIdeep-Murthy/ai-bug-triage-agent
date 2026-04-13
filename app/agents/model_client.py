"""Model service abstraction and Ollama client implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from app.core.config import Settings, get_settings


@dataclass
class ModelResponse:
    content: str
    model_name: str
    raw: dict[str, Any] | None = None


class ModelClient(Protocol):
    """Contract for model providers used by analysis orchestration."""

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict[str, Any],
        model_name: str | None = None,
    ) -> ModelResponse:
        """Generate model output intended to conform to a JSON schema."""


class OllamaModelClient:
    """Ollama-backed model client with structured output hinting."""

    def __init__(self, settings: Settings | None = None, timeout_seconds: float = 60.0):
        self.settings = settings or get_settings()
        self.timeout_seconds = timeout_seconds

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict[str, Any],
        model_name: str | None = None,
    ) -> ModelResponse:
        chosen_model = model_name or self.settings.model_name
        base_url = self.settings.ollama_base_url.rstrip("/")
        url = f"{base_url}/api/chat"

        payload = {
            "model": chosen_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            # Ollama structured output hinting.
            "format": json_schema,
            "stream": False,
        }

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            raw = response.json()

        message = raw.get("message", {}) if isinstance(raw, dict) else {}
        content = message.get("content", "") if isinstance(message, dict) else ""
        return ModelResponse(content=str(content), model_name=chosen_model, raw=raw)

