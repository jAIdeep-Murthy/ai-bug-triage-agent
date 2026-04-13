# User Stories

**Constraints (unchanged from approved requirements)**  
Local/free stack; FastAPI + SQLAlchemy + SQLite MVP; no vector DB MVP; Ollama local (`qwen2.5:7b` default); Jira via env vars with mock fallback; JSON-first LLM output with repair fallback; feedback persisted without ranking effect; seeded synthetic data + committed artifacts; security baseline enforced; no autonomous fixes, no production automation, no auto-close/deploy.

**Persona tags**: [Alex] engineer triage, [Jordan] platform, [Sam] reviewer.

**Dependency notation**: `→` means “depends on” (blocked until prerequisite stories are done).

---

## Phase 1 — Project foundation and API shell (Backend)

### US-B01 — Health and readiness
**As** [Jordan], **I want** a `GET /health` endpoint **so that** I can verify the process is running and configuration loads without exposing secrets.

**Acceptance criteria**
- Returns JSON with status (e.g. `ok`) and non-sensitive build/version or config flags (e.g. mock vs live Jira mode).
- Does not log or return API tokens or raw env secrets.
- Returns HTTP 200 when the app is up.

**Depends on**: —  
**Unlocks**: US-B02, US-B03

---

### US-B02 — Configuration and security hygiene
**As** [Jordan], **I want** all secrets and URLs loaded from environment variables **so that** nothing sensitive is hardcoded and defaults are safe for local dev.

**Acceptance criteria**
- Documented vars: `JIRA_BASE_URL`, `JIRA_EMAIL` or `JIRA_USER`, `JIRA_API_TOKEN`, `OLLAMA_BASE_URL`, `MODEL_NAME` (default `qwen2.5:7b`), DB URL for SQLite.
- Central settings module; validation on startup with clear error messages (no secret values in messages).
- `.env.example` lists keys without real values.

**Depends on**: US-B01  
**Unlocks**: US-B06, US-B09

---

### US-B03 — Application layering and logging
**As** [Sam], **I want** routers, services, integrations, and agents separated **so that** the codebase stays maintainable and testable.

**Acceptance criteria**
- FastAPI routers are thin; business logic in `services/`; Jira HTTP in `integrations/`; LLM prompts/orchestration in `agents/` (or equivalent).
- Structured logging with request/correlation id where practical; no tokens or full Jira payloads logged at info level by default.

**Depends on**: US-B01  
**Unlocks**: US-B04–US-B14

---

## Phase 2 — Synthetic data and retrieval (Backend MVP)

### US-B04 — Seeded synthetic datasets
**As** [Alex], **I want** realistic fake historical bugs, runbooks, configs, and log snippets **so that** retrieval demos work without real company data.

**Acceptance criteria**
- Generator script is **seeded** and reproducible; outputs are **committed** under `data/` (JSON or CSV per repo convention).
- At least ~100 historical bug records; 10–20 items each for runbooks, configs, logs (per requirements).
- Schema is documented briefly in README or `docs/`.

**Depends on**: US-B02  
**Unlocks**: US-B05

---

### US-B05 — Keyword retrieval and ranking (no vector DB)
**As** [Alex], **I want** keyword + metadata search over synthetic corpora **so that** I get top-N similar incidents with explainable scores.

**Acceptance criteria**
- No vector database; scoring uses token overlap / keyword match + filters (e.g. labels, service, environment, error signature fields when present).
- Returns ranked candidates with short **why** (e.g. matched terms or fields).
- Unit tests cover scoring edge cases (empty query, no matches, tie handling).

**Depends on**: US-B04, US-B03  
**Unlocks**: US-B08, US-B11, optional US-B15

---

## Phase 3 — Jira ingestion and normalization (Backend MVP)

### US-B06 — Jira client: live + mock fallback
**As** [Jordan], **I want** a Jira REST client that uses real credentials when set and falls back to mocks otherwise **so that** local development works without a live Jira.

**Acceptance criteria**
- When required env vars are present: fetch issue by key/id, comments, and attachment metadata (metadata sufficient for MVP).
- When vars missing: deterministic mock responses; mode is explicit in logs and/or health.
- All auth via headers; no credentials in code or logs.

**Depends on**: US-B02, US-B03  
**Unlocks**: US-B07, US-B08

---

### US-B07 — Normalize Jira payloads to internal issue model
**As** [Alex], **I want** webhook payloads and REST responses mapped to one internal schema **so that** analysis and retrieval inputs are consistent.

**Acceptance criteria**
- Pydantic models for normalized issue: identity, title/body, labels, status, assignee/reporter fields as applicable, comments list, derived text for retrieval (e.g. concatenated description + comments).
- Webhook handler extracts issue key and relevant fields from typical Jira Cloud webhook JSON.
- Tests for at least one sample webhook fixture and one REST-shaped fixture.

**Depends on**: US-B06  
**Unlocks**: US-B08, US-B10

---

### US-B08 — Webhook and analyze-by-id entry points
**As** [Jordan], **I want** `POST /webhooks/jira` and `GET /issues/{issue_id}/analyze` **so that** issues can drive analysis from events or manual triggers.

**Acceptance criteria**
- Webhook returns quickly with acknowledgment (202/200 per design) and persists/triggers analysis pipeline asynchronously or synchronously with documented behavior.
- Analyze-by-id fetches issue via US-B06, normalizes (US-B07), runs retrieval (US-B05), and invokes analysis (US-B10–B11).
- Input validation on paths and payloads; safe errors (no stack traces to client in production mode).

**Depends on**: US-B05, US-B07  
**Unlocks**: US-B12, US-B13

---

## Phase 4 — AI analysis, guardrails, persistence (Backend MVP)

### US-B09 — Ollama model service abstraction
**As** [Jordan], **I want** LLM calls behind an interface with configurable base URL and model **so that** I can swap models or point to another local server later.

**Acceptance criteria**
- Default model name `qwen2.5:7b` when `MODEL_NAME` unset.
- Clear timeouts and error handling; failures surfaced as structured API errors.
- LangGraph-ready: orchestration class can be replaced without changing HTTP layer.

**Depends on**: US-B02  
**Unlocks**: US-B10

---

### US-B10 — Structured analysis output (JSON-first + repair)
**As** [Alex], **I want** the model to return analysis as JSON matching a defined schema **so that** downstream consumers are reliable.

**Acceptance criteria**
- Primary path: parse model output as JSON; validate with Pydantic.
- Fallback: repair/extract JSON from noisy output; log repair path usage (no secrets).
- Required fields per requirements: `issue_id`, `summary`, `category`, `severity`, `likely_owner_team`, `confidence`, `possible_root_causes`, `evidence`, `similar_issues`, `recommended_steps`, `missing_information`, `jira_comment_draft`, `created_at` (or server-set `created_at` if model omits).
- Tests for valid JSON, malformed JSON with repair, and schema validation failures.

**Depends on**: US-B09, US-B05, US-B07  
**Unlocks**: US-B11, US-B12

---

### US-B11 — Guardrails in prompts and responses
**As** [Alex], **I want** the system to enforce human-in-the-loop behavior **so that** we never claim the bug is fixed or auto-resolve Jira issues.

**Acceptance criteria**
- Prompt instructs: use **only** provided evidence; include confidence; list missing info; no fabricated incidents.
- Response always includes uncertainty language when confidence is below a configurable threshold; “needs human review” flag or equivalent in JSON.
- No wording that states resolution or closure; no autonomous Jira transitions in code.

**Depends on**: US-B10  
**Unlocks**: US-B12, US-D01

---

### US-B12 — Persist analyses and feedback (SQLite)
**As** [Jordan], **I want** analyses and user feedback stored in SQLite **so that** I can audit runs and improve the product later.

**Acceptance criteria**
- SQLAlchemy models and migrations or create-on-start for MVP SQLite file path via env.
- Store latest (or versioned) analysis per issue id; store feedback records from `POST /feedback` with timestamp; **no** retrieval re-ranking from feedback in MVP.
- Clear path to PostgreSQL documented (connection string only; no mandatory impl).

**Depends on**: US-B02, US-B08, US-B10  
**Unlocks**: US-B13, US-D01

---

### US-B13 — Report and feedback API
**As** [Alex], **I want** `GET /issues/{issue_id}/report` and `POST /feedback` **so that** I can retrieve the latest triage and record whether it was helpful.

**Acceptance criteria**
- Report returns stored analysis JSON (or 404 if none) with consistent schema.
- Feedback endpoint validates body (rating/text/issue id); persists only; optional idempotent behavior documented.
- Tests for happy paths and validation failures.

**Depends on**: US-B12  
**Unlocks**: US-D01, US-Q02

---

### US-B14 — Optional API: comment draft and similar search
**As** [Alex], **I want** optional `POST /jira/{issue_id}/comment-draft` and `GET /search/similar` **so that** I can demo Jira comment drafts and ad-hoc similarity search.

**Acceptance criteria**
- If implemented: comment draft does **not** auto-post unless separate explicit call documented; default is draft-only return.
- Similar search uses same retrieval engine as US-B05; query params validated and bounded.
- Documented as optional in README.

**Depends on**: US-B05, US-B06 (for draft content context), US-B10  
**Unlocks**: US-D02 (optional)

---

## Phase 5 — Quality, security verification, documentation (Cross-cutting; Backend-first)

### US-Q01 — Automated tests for core paths
**As** [Sam], **I want** Pytest coverage for retrieval, schema validation, and key API flows **so that** regressions are caught early.

**Acceptance criteria**
- Tests for retrieval scoring, JSON repair, webhook/analyze/report/feedback routes (with mocks).
- CI-ready command documented (`pytest`).

**Depends on**: US-B05, US-B08, US-B10, US-B13  
**Unlocks**: US-Q02

---

### US-Q02 — README and developer docs
**As** [Jordan], **I want** setup instructions for Ollama, Jira webhook, and env vars **so that** anyone can run the stack locally.

**Acceptance criteria**
- README covers: install, `uvicorn`, Ollama model pull, `.env` from `.env.example`, SQLite location, running tests.
- Security notes: no paid APIs, local-only defaults, no autonomous actions.

**Depends on**: US-B02, US-Q01  
**Unlocks**: —

---

## Phase 6 — Streamlit dashboard (After Backend MVP)

### US-D01 — View triage reports in Streamlit
**As** [Alex], **I want** a Streamlit app that lists issues with stored analyses and shows detail **so that** I can review triage without raw curl/JSON.

**Acceptance criteria**
- Reads from backend API (same host/port configurable); displays structured fields and confidence.
- Does not embed secrets; uses same env pattern or API base URL env.
- Available after backend endpoints US-B13 are stable.

**Depends on**: US-B13, US-B11  
**Unlocks**: US-D02

---

### US-D02 — Trigger or refresh analysis from UI (optional within dashboard phase)
**As** [Alex], **I want** to enter a Jira issue id and request analysis from the dashboard **so that** I can demo end-to-end without external tools.

**Acceptance criteria**
- Calls `GET /issues/{id}/analyze` or documented equivalent; shows loading/error states.
- No autonomous Jira writes; any “post comment” is out of scope or explicitly disabled in UI for MVP.

**Depends on**: US-D01, US-B08  
**Unlocks**: —

---

## Dependency summary (story IDs)

| Story | Depends on |
|-------|------------|
| US-B01 | — |
| US-B02 | US-B01 |
| US-B03 | US-B01 |
| US-B04 | US-B02 |
| US-B05 | US-B03, US-B04 |
| US-B06 | US-B02, US-B03 |
| US-B07 | US-B06 |
| US-B08 | US-B05, US-B07 |
| US-B09 | US-B02 |
| US-B10 | US-B05, US-B07, US-B09 |
| US-B11 | US-B10 |
| US-B12 | US-B02, US-B08, US-B10 |
| US-B13 | US-B12 |
| US-B14 | US-B05, US-B06, US-B10 |
| US-Q01 | US-B05, US-B08, US-B10, US-B13 |
| US-Q02 | US-B02, US-Q01 |
| US-D01 | US-B11, US-B13 |
| US-D02 | US-D01, US-B08 |

### Textual dependency chain (critical path)

`US-B01 → US-B02 → US-B04 → US-B05`  
`US-B01 → US-B03` (parallel)  
`US-B02 + US-B03 → US-B06 → US-B07 → US-B08`  
`US-B02 → US-B09 → US-B10` (parallel with Jira path after US-B05/US-B07)  
`US-B08 + US-B10 → US-B11 → US-B12 → US-B13 → US-D01`  
`US-Q01` after core backend; `US-Q02` after `US-Q01`
