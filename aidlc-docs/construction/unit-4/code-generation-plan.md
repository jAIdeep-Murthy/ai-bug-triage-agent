# Unit 4 - Code Generation Plan (Ollama Abstraction + Analysis Orchestration)

**Assigned stories**: US-B09, US-B10, US-B11  
**Scope**: Ollama model abstraction, analysis output schema, custom orchestration, JSON-first parsing with repair fallback, diagnostics, and tests.

## Files to create/modify and responsibilities

- [x] `app/schemas/analysis.py`
  - Canonical analysis output schema with required fields and human-in-the-loop guardrails.
- [x] `app/agents/prompts.py`
  - Prompt builders for evidence-grounded triage and strict JSON expectations.
- [x] `app/agents/model_client.py`
  - Model service abstraction (`ModelClient` protocol) + Ollama implementation.
  - Default model stays `qwen2.5:7b` via `Settings.model_name`.
- [x] `app/services/json_repair.py`
  - Fallback JSON extraction/repair utility and parse diagnostics.
- [x] `app/agents/orchestrator.py`
  - Custom orchestration flow (LangGraph-ready interface) from normalized issue + retrieval evidence to validated analysis output.
- [x] `tests/test_analysis_schema.py`
  - Schema and fallback tests for valid/malformed model output handling.
- [x] `tests/test_orchestrator.py`
  - Orchestration test using fake model client (no live Ollama dependency).

## Model service abstraction design

- [x] `ModelClient` protocol:
  - `generate_json(system_prompt, user_prompt, schema, model_name)` returns raw model output text and metadata.
- [x] `OllamaModelClient` implementation:
  - Calls Ollama chat API with `format=schema` when possible for structured output.
  - Uses configurable `OLLAMA_BASE_URL` and `MODEL_NAME`.
  - Returns clean diagnostics (no secret leakage).

## Analysis output schema design

- [x] Include required fields:
  - `issue_id`, `summary`, `category`, `severity`, `likely_owner_team`, `confidence`,
    `possible_root_causes`, `evidence`, `similar_issues`, `recommended_steps`,
    `missing_information`, `jira_comment_draft`, `created_at`
- [x] Add guardrail fields:
  - `needs_human_review` derived from confidence threshold
  - uncertainty note (non-final, no “fixed” claims)

## Orchestration flow (custom, LangGraph-ready)

- [x] Build prompt from normalized issue + top retrieval evidence.
- [x] Request structured JSON output from model client.
- [x] Validate with Pydantic schema.
- [x] On parse/validation failure, use repair fallback and re-validate.
- [x] Return analysis + diagnostics (e.g., `used_repair`, `validation_errors`).

## JSON validation / repair fallback approach

- [x] Primary path: `AnalysisResult.model_validate_json(raw_text)`
- [x] Fallback path:
  - extract likely JSON object block from text
  - normalize common issues (trailing commas, code-fence wrapping)
  - re-validate via Pydantic
- [x] Keep diagnostics explicit and clean.

## Tests to add

- [x] `tests/test_analysis_schema.py`
  - valid JSON -> parsed successfully
  - malformed JSON with code fences -> repaired successfully
  - invalid schema -> raises clear error
- [x] `tests/test_orchestrator.py`
  - fake model client success path
  - fake model client malformed output path (repair engaged)
  - asserts human-in-the-loop behavior (`needs_human_review` when low confidence)

## Assumptions and deferred items

Assumptions
- [x] Unit 4 tests avoid live Ollama by default (fake/stub model client).
- [x] No persistence or API wiring yet; orchestration is callable as service layer logic.

Deferred (not Unit 4)
- [ ] SQLite persistence (Unit 5)
- [ ] Webhook endpoint wiring and API integration for analysis execution (Unit 5)
- [ ] Streamlit UI (Unit 7)
- [ ] LangGraph implementation (keep interfaces ready)

## Execution constraints

- [x] Execute Unit 4 only.
- [x] Do not begin Unit 5 without explicit user approval.
