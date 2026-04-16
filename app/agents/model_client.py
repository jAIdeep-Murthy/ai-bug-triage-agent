"""Model service abstraction and Ollama client implementation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from app.core.config import Settings, get_settings


class OllamaConnectionError(RuntimeError):
    """Raised when Ollama is unreachable or returns an unexpected error."""


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

    def __init__(self, settings: Settings | None = None, timeout_seconds: float = 300.0):
        self.settings = settings or get_settings()
        self.timeout_seconds = timeout_seconds

    def ping(self) -> bool:
        """Return True if Ollama is reachable and configured model is available.

        Raises:
            OllamaConnectionError: If Ollama is unreachable or the model is not available.
        """
        base_url = self.settings.ollama_base_url.rstrip("/")
        configured = self.settings.model_name
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{base_url}/api/tags")
                response.raise_for_status()
                tags = response.json()
            model_names = [m.get("name", "") for m in tags.get("models", [])]

            configured_family = configured.split(":", 1)[0]
            available = any(
                name == configured or name.startswith(configured_family)
                for name in model_names
            )
            if not available:
                raise OllamaConnectionError(
                    f"Model '{configured}' not found in Ollama. Run: ollama pull {configured}"
                )
            return True
        except httpx.ConnectError as exc:
            raise OllamaConnectionError(
                f"Cannot reach Ollama at {base_url}. Ensure 'ollama serve' is running."
            ) from exc
        except httpx.TimeoutException as exc:
            raise OllamaConnectionError(
                f"Timed out while contacting Ollama at {base_url}."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise OllamaConnectionError(
                f"Ollama returned HTTP {exc.response.status_code}."
            ) from exc

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

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                raw = response.json()
        except httpx.ConnectError as exc:
            raise OllamaConnectionError(
                f"Cannot reach Ollama at {base_url}. Ensure 'ollama serve' is running."
            ) from exc
        except httpx.TimeoutException as exc:
            raise OllamaConnectionError(
                "Timed out while waiting for Ollama model response."
            ) from exc

        message = raw.get("message", {}) if isinstance(raw, dict) else {}
        content = message.get("content", "") if isinstance(message, dict) else ""
        if isinstance(content, (dict, list)):
            content_text = json.dumps(content)
        else:
            content_text = str(content)

        # Best-effort normalization for common model output quirks while keeping schemas strict.
        # - Some models return confidence on a 0-100 scale; convert to 0-1 when appropriate.
        try:
            parsed = json.loads(content_text)
            if isinstance(parsed, dict):
                conf = parsed.get("confidence")
                if isinstance(conf, (int, float)) and conf > 1 and conf <= 100:
                    parsed["confidence"] = float(conf) / 100.0
                steps = parsed.get("recommended_steps")
                if steps is None:
                    parsed["recommended_steps"] = [
                        "Collect relevant logs and error snippets, then correlate with deploy timing and upstream dependency health."
                    ]
                elif isinstance(steps, list) and len(steps) == 0:
                    parsed["recommended_steps"] = [
                        "Collect relevant logs and error snippets, then correlate with deploy timing and upstream dependency health."
                    ]

                similar = parsed.get("similar_issues")
                evidence = parsed.get("evidence")
                if (similar is None or (isinstance(similar, list) and len(similar) == 0)) and isinstance(
                    evidence, list
                ):
                    extracted: list[str] = []
                    for item in evidence:
                        if not isinstance(item, str):
                            continue
                        extracted.extend(re.findall(r"JDT-\\d+", item))
                    if extracted:
                        # Keep first-seen order and ensure distinct.
                        seen: set[str] = set()
                        parsed["similar_issues"] = [x for x in extracted if not (x in seen or seen.add(x))]

                content_text = json.dumps(parsed)
        except Exception:
            # Leave content_text as-is; upstream validator/repair will handle failures.
            pass
        return ModelResponse(content=content_text, model_name=chosen_model, raw=raw)

