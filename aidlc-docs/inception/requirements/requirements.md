# AI Bug Triage and Resolution Service - Requirements

## Intent Analysis Summary
- **User Request**: Build a production-style, resume-quality AI bug triage and resolution recommendation service integrated with Jira.
- **Request Type**: New Project
- **Scope Estimate**: Multiple components (API, integration, retrieval, AI analysis, persistence, dashboard, tests, docs)
- **Complexity Estimate**: Complex
- **Depth**: Standard to Comprehensive (due integration, AI pipeline, and security constraints)

## Product Goal
Create a local-first service that reacts to Jira bug activity, gathers synthetic organizational context, performs evidence-grounded AI triage, and provides structured debugging recommendations with human-in-the-loop guardrails.

## Non-Goals
- No autonomous bug fixing
- No code deployment automation
- No direct production system modifications
- No paid model APIs
- No vector database in MVP

## Functional Requirements

### FR-01 API Surface
Provide FastAPI endpoints:
- `GET /health`
- `POST /webhooks/jira`
- `GET /issues/{issue_id}/analyze`
- `GET /issues/{issue_id}/report`
- `POST /feedback`

Optional endpoints:
- `POST /jira/{issue_id}/comment-draft`
- `GET /search/similar?query=...`

### FR-02 Jira Ingestion
- Consume Jira webhook payloads for issue create/update events.
- Fetch Jira issue details by ID using Jira Cloud REST API.
- Fetch issue comments and metadata.
- Support attachment metadata retrieval (optional in MVP).
- Use env vars for credentials/config only.

### FR-03 Dual-Mode Jira Access
- Default to real Jira integration when env vars are configured.
- Provide fallback mock mode when Jira env vars are absent.
- Keep behavior explicit and observable via logs and API responses.

### FR-04 Internal Normalization
Normalize incoming issue data into internal schema with fields for:
- Issue identity and source metadata
- Title, description, labels, status, assignee/reporter metadata
- Comments
- Derived error signatures/features for retrieval

### FR-05 Context and Dataset Layer
Load synthetic datasets from `/data`:
- Historical bugs (`~100+`)
- Runbooks (`10-20`)
- Config issue examples (`10-20`)
- Log/error snippets (`10-20`)

### FR-06 Retrieval Without Vector DB
- Implement keyword + metadata retrieval only.
- Score using title/summary/error signature overlap plus labels/service/environment matches.
- Return top-N candidates with evidence and scoring rationale.

### FR-07 Analysis Pipeline
- Implement custom Python orchestration (not LangGraph-first), but with abstractions that keep migration to LangGraph straightforward.
- Inputs: normalized issue + retrieved evidence.
- Output: strict structured analysis object with required fields:
  - `issue_id`, `summary`, `category`, `severity`, `likely_owner_team`, `confidence`,
  - `possible_root_causes`, `evidence`, `similar_issues`, `recommended_steps`,
  - `missing_information`, `jira_comment_draft`, `created_at`

### FR-08 Model Integration
- Use local Ollama through model service abstraction.
- Default model: `qwen2.5:7b`.
- Respect `OLLAMA_BASE_URL` and `MODEL_NAME` env vars.

### FR-09 JSON-First Reliability
- Enforce JSON-first LLM response contract.
- Add repair fallback parser for malformed JSON.
- Persist parse and repair diagnostics for observability.

### FR-10 Persistence
- Use SQLite in MVP via SQLAlchemy.
- Persist analysis reports and feedback.
- Feedback persistence is storage-only in MVP (no retrieval-rerank effect yet).
- Keep architecture ready for PostgreSQL migration later.

### FR-11 Output Channels
- Return structured JSON via API.
- Provide human-readable report endpoint/view.
- Support optional Jira comment draft generation/posting behavior with explicit human review framing.

### FR-12 Dashboard
- Build Streamlit dashboard after backend completion.
- Dashboard should display issue analysis, evidence, confidence, and recommended steps.

### FR-13 Testing
Add Pytest coverage for:
- Retrieval scoring and filtering
- Analysis pipeline schema validation
- JSON-repair fallback behavior
- Core API happy path

### FR-14 Documentation
Provide:
- Setup and run instructions
- Environment variable configuration
- Jira webhook setup
- Local Ollama setup
- Architecture and security notes

## Non-Functional Requirements

### NFR-01 Maintainability
- Clear layered architecture (`api`, `services`, `agents`, `integrations`, `retrieval`, `db`, etc.).
- Strong separation of concerns.
- Small focused modules.

### NFR-02 Code Quality
- Python 3.11+
- Type hints throughout
- Docstrings for public interfaces
- Consistent structured logging

### NFR-03 Security Baseline (Enabled)
- Security extension rules are enabled for this project.
- No hardcoded credentials.
- Input validation for API payloads and query parameters.
- Safe error handling and fail-closed behavior.
- Dependency pinning and reproducible local setup.
- Avoid sensitive data leakage in logs.

### NFR-04 Safety and Governance
- Human-in-the-loop always.
- Never claim issue is fixed.
- Low-confidence analyses explicitly flagged for human review.
- No autonomous production actions.

### NFR-05 Local Cost and Access
- Must run fully with free/open-source tooling on local machine.
- No paid LLM APIs.

## Data Requirements
- Include seeded synthetic data generator scripts.
- Commit generated synthetic files for deterministic demo behavior.
- Data must remain synthetic only; no real organizational data.

## Architecture Constraints
- FastAPI + Pydantic + SQLAlchemy + SQLite (MVP).
- Custom orchestration service that is LangGraph-ready via clear orchestration/model interfaces.
- No vector DB in MVP.
- Streamlit UI introduced after backend implementation.

## Acceptance Criteria (MVP)
1. A Jira issue can be analyzed from issue ID or webhook payload.
2. System retrieves relevant synthetic incidents and evidence.
3. LLM analysis returns schema-compliant JSON (or repaired fallback).
4. Analysis and feedback are stored in SQLite.
5. API exposes health, analyze, report, webhook, and feedback routes.
6. Dashboard can browse and view analysis outputs.
7. README enables local run with environment variables and Ollama.
8. Guardrails are visible in outputs (confidence + uncertainty + no auto-fix claims).

## Open Decisions Deferred
- Optional endpoint inclusion (`comment-draft`, `search/similar`) can be finalized during implementation.
- PostgreSQL migration path documented but not implemented in MVP.
