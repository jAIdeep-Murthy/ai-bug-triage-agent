"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.feedback import router as feedback_router
from app.api.health import router as health_router
from app.api.issues import router as issues_router
from app.api.webhooks import router as webhooks_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Configure logging once at startup."""
    configure_logging()
    init_db()
    settings = get_settings()
    logger.info(
        "Starting %s v%s | jira_mode=%s | model=%s",
        settings.app_name,
        settings.app_version,
        settings.jira_mode,
        settings.model_name,
    )
    yield
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """Build and return the FastAPI application."""
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    application.include_router(health_router)
    application.include_router(webhooks_router)
    application.include_router(issues_router)
    application.include_router(feedback_router)
    return application


app = create_app()
