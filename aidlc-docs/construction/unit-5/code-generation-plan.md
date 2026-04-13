# Unit 5 - Code Generation Plan (SQLite Persistence + API Wiring + Orchestration Integration)

**Assigned stories**: US-B08, US-B12, US-B13  
**Scope**: SQLite persistence/store abstraction, API route wiring, and end-to-end service flow integration (issue fetch -> normalize -> retrieve -> analyze -> persist -> report).

## 1) Files to create/modify

- [x] `requirements.txt` (modify)
  - Add SQLAlchemy dependency for SQLite persistence.
- [x] `app/db/base.py` (create)
  - Declarative Base for ORM models.
- [x] `app/db/session.py` (create)
  - Engine/session factory and `init_db()` utilities.
- [x] `app/models/analysis.py` (create)
  - ORM model for persisted analysis report.
- [x] `app/models/feedback.py` (create)
  - ORM model for persisted feedback records.
- [x] `app/services/analysis_store.py` (create)
  - Repository abstraction for writing/reading analysis records.
- [x] `app/services/feedback_store.py` (create)
  - Repository abstraction for feedback persistence.
- [x] `app/services/triage_pipeline.py` (create)
  - Integrates Jira fetch + normalization + retrieval + orchestration + persistence.
- [x] `app/api/deps.py` (create)
  - Dependency providers for stores and pipeline (overridable in tests).
- [x] `app/api/issues.py` (create)
  - `GET /issues/{issue_id}/analyze` and `GET /issues/{issue_id}/report`.
- [x] `app/api/webhooks.py` (create)
  - `POST /webhooks/jira` (parse webhook issue key and trigger analysis flow).
- [x] `app/api/feedback.py` (create)
  - `POST /feedback` with strict request validation.
- [x] `app/schemas/api.py` (create)
  - Request/response schemas for feedback and API responses.
- [x] `app/main.py` (modify)
  - Include new routers and initialize DB on startup.
- [x] `tests/test_api_issues.py` (create)
  - API tests for analyze/report/feedback/webhook success + errors.
- [x] `tests/test_persistence.py` (create)
  - Store-level persistence tests using SQLite.

## 2) SQLite / SQLAlchemy model design

- [x] `AnalysisRecord` table:
  - `id` (PK), `issue_id` (indexed), `issue_key`, `summary`, `category`, `severity`,
    `likely_owner_team`, `confidence`, `needs_human_review`, `analysis_json`, `created_at`
- [x] `FeedbackRecord` table:
  - `id` (PK), `issue_id` (indexed), `rating`, `comment`, `created_at`
- [x] SQLite only in Unit 5 via `DATABASE_URL` (default already configured).
- [x] Keep repository interface clean for future PostgreSQL migration.

## 3) API route wiring design

- [x] `GET /issues/{issue_id}/analyze`
  - Input validation on `issue_id`.
  - Run triage pipeline, persist analysis, return analysis JSON + diagnostics.
  - Error mapping: missing issue (404), Jira/model/network failures (502/504), validation failures (422/500 as appropriate).
- [x] `GET /issues/{issue_id}/report`
  - Return most recent persisted analysis for issue.
  - 404 when report missing.
- [x] `POST /webhooks/jira`
  - Validate payload shape, extract issue key, invoke analyze path, return accepted/result.
  - 400 when issue key missing/invalid.
- [x] `POST /feedback`
  - Validate payload via Pydantic schema.
  - Persist only (no reranking effect).
  - Return acknowledgement + feedback id.

## 4) Orchestration integration flow

- [x] Pipeline flow:
  1. Jira client fetch issue bundle
  2. Normalize to internal issue
  3. Build retrieval query and run keyword retrieval
  4. Run analysis orchestrator
  5. Persist analysis via `AnalysisStore`
  6. Return analysis run result
- [x] Keep integration testable via dependency providers and injectable pipeline components.

## 5) Tests to add

- [x] `tests/test_persistence.py`
  - Create SQLite DB, insert analysis, fetch latest by issue id.
  - Insert feedback, verify storage.
- [x] `tests/test_api_issues.py`
  - Analyze success using dependency override fake pipeline/store.
  - Report 404 when missing.
  - Feedback validation and persistence success.
  - Webhook invalid payload -> 400.
  - Graceful error mapping for pipeline exceptions.

## 6) Assumptions and deferred items

Assumptions
- [x] Unit 5 tests will use mock/injected pipeline; no live Ollama/Jira required.
- [x] No migration tool required yet; create tables via SQLAlchemy metadata.

Deferred (not Unit 5)
- [ ] PostgreSQL implementation/migrations
- [ ] Streamlit dashboard
- [ ] Feedback-driven retrieval reranking
- [ ] Advanced webhook async queueing

## 7) Execution constraints

- [x] Execute Unit 5 only.
- [x] Keep security rules active (input validation, safe logs, graceful failures).
- [x] Do not begin Unit 6 without explicit user approval.
