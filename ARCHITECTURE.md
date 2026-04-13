# ARCHITECTURE

## Layers

- **API Layer (`app/api`)**
  - HTTP endpoints for health, webhook intake, analyze/report, feedback.
- **Integration Layer (`app/integrations`)**
  - Jira client with env-driven live mode and deterministic mock fallback.
- **Normalization Layer (`app/services/issue_normalizer.py`)**
  - Converts raw Jira structures into a clean internal typed issue model.
- **Retrieval Layer (`app/retrieval`)**
  - Keyword + metadata retrieval over synthetic datasets.
- **Agent/Orchestration Layer (`app/agents`)**
  - Model abstraction (Ollama) and custom orchestration with schema validation.
- **Persistence Layer (`app/db`, `app/models`, `app/services/*_store.py`)**
  - SQLite persistence for analyses and feedback through store abstractions.
- **Schema Layer (`app/schemas`)**
  - Request/response/domain contracts for strict validation.

## Data flow

1. Request enters API (`/issues/{id}/analyze` or `/webhooks/jira`).
2. Jira issue is fetched (live/mock).
3. Raw issue is normalized into internal model.
4. Retrieval finds similar incidents from synthetic datasets.
5. Orchestrator calls model abstraction and validates JSON output.
6. JSON repair fallback is applied when needed.
7. Analysis is persisted to SQLite.
8. API returns structured response.

## Module responsibilities

- `app/core/config.py`: env-based settings and mode selection.
- `app/core/logging.py`: consistent logging setup.
- `app/services/triage_pipeline.py`: end-to-end orchestration glue.
- `app/services/analysis_store.py`: analysis repository abstraction.
- `app/services/feedback_store.py`: feedback storage abstraction.
- `app/services/json_repair.py`: JSON repair helpers.
- `app/agents/model_client.py`: model service contract + Ollama implementation.
- `app/agents/orchestrator.py`: custom, LangGraph-ready orchestration flow.

## Design goals

- Clear separation of concerns.
- Testability via dependency injection and typed schemas.
- Local-first developer experience.
- Safe, human-supervised AI behavior.
