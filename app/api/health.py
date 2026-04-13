"""Health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Return service status and non-sensitive configuration flags."""
    settings = get_settings()
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "jira_mode": settings.jira_mode,
        "model_name": settings.model_name,
    }
