"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Secrets must only appear in env, never in code."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Bug Triage API"
    app_version: str = "0.1.0"

    jira_base_url: str | None = None
    jira_email: str | None = None
    jira_user: str | None = None
    jira_api_token: str | None = None

    ollama_base_url: str = "http://127.0.0.1:11434"
    model_name: str = "qwen2.5:7b"

    # When enabled, analysis runs without calling Ollama and returns a realistic
    # hardcoded analysis (useful for local demos / offline development).
    demo_mode: bool = False

    vector_search_enabled: bool = True
    chroma_db_path: str = "data/chroma_db"

    database_url: str = "sqlite:///./data/bug_triage.db"

    @property
    def jira_mode(self) -> Literal["live", "mock"]:
        """Return live Jira only when all required credentials are present."""
        if (
            self.jira_base_url
            and self.jira_api_token
            and (self.jira_email or self.jira_user)
        ):
            return "live"
        return "mock"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
