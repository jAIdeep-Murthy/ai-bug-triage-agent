"""Health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.agents.model_client import OllamaConnectionError, OllamaModelClient
from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, object]:
    """Return service status and non-sensitive configuration flags."""
    settings = get_settings()
    response: dict[str, object] = {
        "status": "ok",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "jira_mode": settings.jira_mode,
        "model_name": settings.model_name,
        "demo_mode": bool(settings.demo_mode),
    }

    try:
        OllamaModelClient(settings=settings).ping()
        response["ollama_status"] = "ok"
    except OllamaConnectionError as exc:
        response["ollama_status"] = "unreachable"
        response["ollama_error"] = str(exc)

    return response
