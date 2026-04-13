# Implementation Units Proposal (awaiting your approval)

**Purpose**: Decompose construction work into units that map to user stories and respect backend-first ordering. **No application code** should start until you approve this list (or request changes).

**Global constraints**: Same as approved requirements — local/free tools, SQLite MVP, no vector DB, Ollama + `qwen2.5:7b` default, Jira env + mock fallback, JSON-first + repair, security baseline, no autonomous fixes or production actions.

---

## Unit 1 — Foundation and API shell
**Stories**: US-B01, US-B02, US-B03  
**Deliverables**: Repo layout (`app/`, `tests/`, `data/`, `dashboard/` placeholder), FastAPI `main`, `/health`, settings module, logging baseline, `.env.example`, `requirements.txt` with pinned versions.

**Exit criteria**: Health passes; settings load; no secrets in repo; layering directories exist.

---

## Unit 2 — Synthetic data + retrieval engine
**Stories**: US-B04, US-B05  
**Deliverables**: Seeded generator scripts; committed `data/*.json`; retrieval module with keyword/metadata scoring; pytest for retrieval.

**Exit criteria**: Deterministic data; top-N results with explainable scores; no vector DB.

---

## Unit 3 — Jira integration and normalization
**Stories**: US-B06, US-B07  
**Deliverables**: Jira REST client + mock mode; Pydantic internal issue model; webhook payload parsing; sample fixtures in `tests/`.

**Exit criteria**: Live path works with env; mock path without env; normalized issue used everywhere downstream.

---

## Unit 4 — Analysis pipeline: Ollama + JSON + guardrails
**Stories**: US-B09, US-B10, US-B11  
**Deliverables**: Model client abstraction (LangGraph-ready); orchestration service; prompts; Pydantic output schema; JSON repair fallback; guardrail fields and prompt rules.

**Exit criteria**: Valid JSON path + repair path tested; low-confidence flagged; no “fixed” claims in contract.

---

## Unit 5 — Persistence + core REST API completion
**Stories**: US-B08, US-B12, US-B13; optional US-B14  
**Deliverables**: SQLAlchemy models + SQLite session; store analysis and feedback; wire `webhooks/jira`, `issues/{id}/analyze`, `issues/{id}/report`, `feedback`; optional endpoints if timeboxed.

**Exit criteria**: End-to-end: issue → retrieve → analyze → persist → report; feedback stored without affecting retrieval rank.

---

## Unit 6 — Tests and documentation hardening
**Stories**: US-Q01, US-Q02  
**Deliverables**: Expanded pytest; README; security-relevant notes (validation, logging, fail-closed errors).

**Exit criteria**: Documented local run; core tests green.

---

## Unit 7 — Streamlit dashboard (after Unit 5+6 stable)
**Stories**: US-D01, US-D02  
**Deliverables**: `dashboard/streamlit_app.py`; config for API base URL; list/detail views; optional “analyze” action.

**Exit criteria**: Dashboard is read-oriented for triage display; no hidden automation.

---

## Suggested implementation order

1 → 2 → 3 → 4 → 5 → 6 → 7

**Parallelism**: Unit 2 can start after Unit 1; Unit 4 can proceed once Unit 2 retrieval API is stable and Unit 3 provides normalized issue fixtures (or temporary fake normalized issues until Unit 3 lands).

---

## Approval

**Please reply with one of:**
- **Approve** — proceed to Workflow Planning / Application Design as per AI-DLC next stage, then begin code in unit order.
- **Request changes** — specify unit splits, scope, or ordering adjustments.
