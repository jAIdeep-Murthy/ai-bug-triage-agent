# Unit 6 - Code Generation Plan (Quality + Docs)

## Scope
- Add/expand tests only (no implementation-logic changes)
- Produce complete project documentation for local use and demo readiness

## Files to create/modify
- [x] `tests/test_retrieval_edges.py`
  - retrieval edge cases: no match, partial match, deterministic tie behavior.
- [x] `tests/test_pipeline_errors.py`
  - pipeline and API-facing error paths: Jira 502, model 504, missing report.
- [x] `tests/test_json_repair_edges.py`
  - JSON repair fallback edge paths.
- [x] `tests/test_feedback_persistence_extra.py`
  - feedback storage behavior checks (storage-only).
- [x] `tests/test_guardrails_extra.py`
  - schema guardrail enforcement tests.
- [x] `README.md`
  - full project documentation with ASCII architecture diagram and usage.
- [x] `SECURITY.md`
  - security policy summary for MVP constraints.
- [x] `ARCHITECTURE.md`
  - layered architecture, data flow, module ownership.

## Doc targets
- [x] Project value proposition and problem statement
- [x] Architecture overview + ASCII diagram
- [x] Tech stack
- [x] Setup/run instructions
- [x] Env var reference
- [x] Jira live/mock configuration
- [x] Ollama setup with `qwen2.5:7b`
- [x] End-to-end triage flow
- [x] API reference + cURL examples + sample responses
- [x] Synthetic dataset notes
- [x] Limitations and future roadmap

## Constraints
- [x] No Streamlit work in Unit 6
- [x] No changes to existing implementation logic

