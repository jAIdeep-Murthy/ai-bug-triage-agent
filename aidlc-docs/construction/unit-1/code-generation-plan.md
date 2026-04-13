# Unit 1 — Code Generation Plan (Foundation and API shell)

**Stories**: US-B01, US-B02, US-B03  
**Scope**: Repository layout, FastAPI entrypoint, environment-driven settings, structured logging, `GET /health` only. **No** Jira, retrieval, DB, or Streamlit.

## Plan checklist

- [x] Add pinned `requirements.txt` (FastAPI, Uvicorn, Pydantic Settings, Pytest, HTTPX for TestClient).
- [x] Add `.env.example` (document keys; no real secrets).
- [x] Add `app/core/config.py` — `Settings` with env vars per requirements; derived `jira_mode` (`live` vs `mock`); never expose tokens.
- [x] Add `app/core/logging.py` — `configure_logging()`; no secret values in log formatters.
- [x] Add `app/main.py` — `create_app()`, lifespan hook to configure logging once.
- [x] Add `app/api/health.py` — `GET /health` returns `status`, non-sensitive config flags.
- [x] Add package layout placeholders: `app/services`, `app/agents`, `app/retrieval`, `app/integrations`, `app/db`, `app/models`, `app/schemas` (empty `__init__.py` only).
- [x] Add `tests/test_health.py` + `tests/conftest.py` if needed.
- [x] Add minimal root `README.md` (how to install deps and run `uvicorn`; pointer to full docs in Unit 6).
- [x] Add `pytest.ini` (test paths / pythonpath).
- [x] Run `pytest` and fix failures.

## Files touched (expected)

| Path | Action |
|------|--------|
| `requirements.txt` | Create |
| `.env.example` | Create |
| `pytest.ini` | Create |
| `README.md` | Create (stub) |
| `app/__init__.py` | Create |
| `app/main.py` | Create |
| `app/core/__init__.py` | Create |
| `app/core/config.py` | Create |
| `app/core/logging.py` | Create |
| `app/api/__init__.py` | Create |
| `app/api/health.py` | Create |
| `app/{services,agents,retrieval,integrations,db,models,schemas}/__init__.py` | Create |
| `tests/__init__.py` | Create (optional) |
| `tests/conftest.py` | Create |
| `tests/test_health.py` | Create |

## Out of scope (defer to later units)

- SQLite, SQLAlchemy, Jira client, webhooks, Ollama, retrieval, Streamlit.

## Approval

User authorized Unit 1 only on 2026-04-02. **Do not start Unit 2** without explicit approval.
