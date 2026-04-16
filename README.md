# AI Bug Triage and Resolution Service

An end-to-end, local-first bug triage service that integrates with Jira, retrieves synthetic historical incident context, runs AI-based triage through Ollama, and returns structured debugging recommendations.

## Why this project matters

Engineering teams lose time when incident context is fragmented across tickets, logs, and tribal knowledge. This project demonstrates a production-style architecture for:
- ingesting Jira issues safely,
- retrieving similar incidents from controlled datasets,
- producing structured AI triage with confidence/uncertainty,
- keeping a strict human-in-the-loop policy.

## Architecture overview

ASCII flow (MVP):

```text
+----------------------+      +----------------------+      +----------------------+
|      Jira Input      | ---> |   Ingestion Layer    | ---> |   Normalized Issue   |
| Issue ID / Webhook   |      | Jira Client (live/   |      | Typed Internal Model |
|                      |      | mock) + Parser       |      |                      |
+----------------------+      +----------------------+      +----------------------+
                                                                  |
                                                                  v
+----------------------+      +----------------------+      +----------------------+
| Synthetic Datasets   | ---> | Retrieval Layer      | ---> | Candidate Evidence   |
| historical/runbooks/ |      | keyword + metadata   |      | ranked incidents +   |
| configs/logs         |      | scoring              |      | snippets             |
+----------------------+      +----------------------+      +----------------------+
                                                                  |
                                                                  v
+----------------------+      +----------------------+      +----------------------+
| Ollama Model Service | ---> | Orchestration Layer  | ---> | Structured Analysis  |
| qwen2.5:7b default   |      | prompt + validate +  |      | confidence + steps + |
| (configurable)       |      | JSON repair fallback |      | human-review flags   |
+----------------------+      +----------------------+      +----------------------+
                                                                  |
                                                                  v
+----------------------+      +----------------------+      +----------------------+
| SQLite Persistence   | <--> | API Layer            | ---> | Client / Dashboard   |
| analysis + feedback  |      | analyze/report/      |      | report + feedback    |
| (storage only)       |      | webhook/feedback     |      |                      |
+----------------------+      +----------------------+      +----------------------+
```

## Tech stack

- Python 3.11+
- FastAPI + Pydantic
- SQLAlchemy + SQLite
- Ollama (local model runtime)
- Pytest
- Streamlit (dashboard; added in Unit 7)

## Project structure (high level)

- `app/api` - FastAPI routes
- `app/core` - settings and logging
- `app/integrations` - Jira integration
- `app/services` - business services, stores, pipeline, repair utilities
- `app/agents` - model abstraction + orchestration
- `app/retrieval` - retrieval engine(s)
- `app/schemas` - typed request/domain/response models
- `app/db`, `app/models` - DB setup + ORM models
- `data` - synthetic datasets
- `dashboard` - Streamlit app
- `tests` - test suite

## Local setup

1. Create/activate a virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and update values as needed.
4. Ensure synthetic datasets exist:
   - `py scripts/generate_synthetic_data.py`

## Run backend

- Start API:
  - `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
- Health check:
  - `curl http://127.0.0.1:8000/health`

## Environment variables reference

- `JIRA_BASE_URL` - Jira Cloud base URL
- `JIRA_EMAIL` or `JIRA_USER` - Jira user
- `JIRA_API_TOKEN` - Jira API token
- `OLLAMA_BASE_URL` - Ollama host (default `http://127.0.0.1:11434`)
- `MODEL_NAME` - model name (default `qwen2.5:7b`)
- `DATABASE_URL` - SQLAlchemy DB URL (default `sqlite:///./data/bug_triage.db`)

## Jira integration configuration

### Mock mode (default fallback)

Used automatically when Jira credentials are incomplete. This is safe for local development and tests.

### Live mode

Set all required Jira vars:
- `JIRA_BASE_URL`
- `JIRA_API_TOKEN`
- one of `JIRA_EMAIL` or `JIRA_USER`

Then `/issues/{issue_id}/analyze` and `/webhooks/jira` will use Jira Cloud REST APIs for issue and comments.

## Ollama setup (`qwen2.5:7b`)

1. Install Ollama from the official site.
2. Pull model:
   - `ollama pull qwen2.5:7b`
3. Ensure Ollama is running and reachable at `OLLAMA_BASE_URL`.
4. Keep `MODEL_NAME=qwen2.5:7b` unless intentionally changed.

## End-to-end triage pipeline

1. Fetch Jira issue (live/mock)
2. Normalize to internal schema
3. Retrieve similar incidents from synthetic datasets
4. Run orchestration:
   - prompt model
   - validate JSON output against Pydantic schema
   - repair fallback when needed
5. Persist analysis in SQLite
6. Return structured analysis response

## API endpoints with examples

### `GET /health`

```bash
curl http://127.0.0.1:8000/health
```

Sample response:

```json
{
  "status": "ok",
  "app_name": "AI Bug Triage API",
  "version": "0.1.0",
  "jira_mode": "mock",
  "model_name": "qwen2.5:7b"
}
```

### `GET /issues/{issue_id}/analyze`

```bash
curl http://127.0.0.1:8000/issues/BUG-123/analyze
```

### `GET /issues/{issue_id}/report`

```bash
curl http://127.0.0.1:8000/issues/10001/report
```

### `POST /webhooks/jira`

```bash
curl -X POST http://127.0.0.1:8000/webhooks/jira \
  -H "Content-Type: application/json" \
  -d '{"payload":{"webhookEvent":"jira:issue_updated","issue":{"key":"BUG-123"}}}'
```

### `POST /feedback`

```bash
curl -X POST http://127.0.0.1:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{"issue_id":"BUG-123","rating":"helpful","comment":"Useful triage"}'
```

## Synthetic dataset description

Generated under `data/` by seeded script:
- `historical_bugs.json` (120 records)
- `runbooks.json` (20 records)
- `configs.json` (15 records)
- `logs.json` (15 records)

Data is fully synthetic and deterministic for reproducible demos.

## Testing

- Run all tests:
  - `py -m pytest`

## Upgrade 1: Live Ollama verification

```bash
# 1. Confirm Ollama is running and model is available
ollama list

# 2. Start the backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 3. Health check — confirm demo_mode: false and ollama_status: "ok"
curl http://127.0.0.1:8000/health

# 4. Run a real analysis
curl http://127.0.0.1:8000/issues/BUG-001/analyze

# 5. Run existing test suite (must still be 33 passing)
pytest --ignore=tests/test_ollama_live.py -v

# 6. Run live end-to-end smoke test (requires ollama serve)
pytest tests/test_ollama_live.py -v -m live
```

## Upgrade 2: Real bug dataset

The synthetic seed data has been replaced with real Eclipse JDT bug
reports from the logpai/bughub open-source dataset.

### Load the real data (run once after pulling this upgrade)

```bash
# Install new dependency
pip install pandas

# Download and load real data (takes ~10 seconds)
python scripts/load_real_data.py

# Verify the data loaded correctly
python scripts/verify_data.py
```

### Dataset
- Source: logpai/bughub (Eclipse JDT, MIT-compatible)
- Records: 500 real resolved bug reports
- Fields: title, description, component, severity, resolution, owner team
- These replace 120 synthetic records

## Limitations (current MVP)

- No authentication/authorization layer.
- SQLite only; no PostgreSQL migration executed yet.
- No production deployment automation.
- Feedback is stored but does not yet adjust retrieval ranking.
- Dashboard is MVP-level (functional, not enterprise UI).

## Future improvements

- PostgreSQL support + migrations
- background job queue for webhook processing
- semantic retrieval backend (while keeping current contract)
- richer Jira workflows (optional comment draft posting path refinement)
- CI pipeline and containerized local stack

## Additional docs

- `ARCHITECTURE.md`
- `SECURITY.md`
- `aidlc-docs/` (planning and workflow artifacts)
