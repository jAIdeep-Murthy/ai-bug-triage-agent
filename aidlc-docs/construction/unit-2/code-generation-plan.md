# Unit 2 — Code Generation Plan (Synthetic Data + Retrieval)

**Assigned Stories**: US-B04, US-B05  
**Unit Goal**: Generate deterministic synthetic datasets (committed JSON files) and implement keyword + metadata retrieval (no vector DB), extensible for future semantic retrieval.

---

## Step 1: Analyze Unit Context
- [x] Read project context from `aidlc-docs/aidlc-state.md` (greenfield; Unit 1 done).
- [x] Confirm constraints: no Jira, no Ollama/model, no SQLite persistence, no Streamlit.
- [x] Confirm retrieval constraint: keyword + metadata only (no vector DB).

---

## Step 2: Create Detailed Unit Code Generation Plan

### Step 2.1 — Synthetic data generation
- [x] Create deterministic generator script: `scripts/generate_synthetic_data.py`
- [x] Generator writes committed dataset files under `data/`:
  - `data/historical_bugs.json` (~100+ incidents)
  - `data/runbooks.json` (10–20)
  - `data/configs.json` (10–20)
  - `data/logs.json` (10–20)
- [x] Use `random.Random(SEED)` and stable JSON output (`sort_keys=True`, fixed field ordering).

### Step 2.2 — Dataset loader (typed)
- [x] Create `app/services/dataset_loader.py` to load the JSON datasets into typed Pydantic models.
- [x] Ensure loader returns clear errors when files are missing.

### Step 2.3 — Retrieval interfaces (extensible)
- [x] Create an extensible retrieval contract in `app/schemas/retrieval.py`:
  - `RetrievalQuery` with fields: `text_query`, `service`, `environment`, `error_signature_tokens` (optional), `labels` (optional)
  - `RetrievedIncident` with fields: `id`, `score`, `match_reasons`, `evidence`
  - `RetrievalResult` with `query` echo + `top_k`
- [x] Create retrieval backend interface in `app/retrieval/retrieval_backend.py` to allow future semantic retrieval backends.

### Step 2.4 — Keyword + metadata retrieval implementation
- [x] Implement `app/retrieval/keyword_retrieval.py`:
  - Tokenization: lower-case, split on non-alphanumerics, filter short tokens.
  - Compute candidate text: title + summary + error_signature + labels.
  - Scoring components (explainable):
    - `error_signature_match` (exact token overlap / substring match, highest weight)
    - `term_overlap` between query tokens and candidate text
    - `service_match` and `environment_match` boosts when query specifies them
    - `category_match` and `label_overlap` smaller boosts
  - Return top-N sorted by `score desc`, then `created_at desc`, then `id` for determinism.

### Step 2.5 — Tests
- [x] Create `tests/test_retrieval.py`:
  - Test dataset integrity (counts and presence of required fields).
  - Test scoring determinism: for a fixed query, the top-1 incident id is stable.
  - Test empty/no-match behavior: returns empty evidence list but valid schema (or safe top-k empty).
  - Test explainability: match_reasons contains at least one reason when overlap exists.

### Step 2.6 — Update progress artifacts
- [x] Update `aidlc-docs/aidlc-state.md` after Unit 2 code generation completes.
- [x] Append to `aidlc-docs/audit.md` with exact actions taken and test results.

---

## Step 3: Unit Stories Traceability
- US-B04: generator + committed dataset files + loader.
- US-B05: keyword retrieval implementation + tests.

---

## Step 4: Expected Files Created/Modified

### Created in workspace root / project code
- `scripts/generate_synthetic_data.py`
- `data/historical_bugs.json`
- `data/runbooks.json`
- `data/configs.json`
- `data/logs.json`
- `app/services/dataset_loader.py`
- `app/retrieval/keyword_retrieval.py`
- `app/schemas/retrieval.py`
- `tests/test_retrieval.py`

### Modified (likely)
- None required in Unit 1 files, except possible addition of `data/` directory placeholder.

---

## Step 5: Assumptions and Deferred Items
Assumptions
- Dataset schemas can be implemented as JSON structures that satisfy retrieval/scoring needs for later analysis.
- For evidence, MVP uses text snippets derived from linked synthetic runbook/config/log IDs stored inside each historical bug record.

Deferred
- Vector/semantic search backends.
- Jira integration (Unit 3).
- Ollama/model integration (Unit 4).
- SQLite persistence (Unit 5).
- Streamlit dashboard (Unit 7).

---

## Approval Gate
This plan is the single source of truth for Unit 2 code generation.  
Proceed only after user explicit approval.

