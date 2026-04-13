# Unit 3 - Code Generation Plan (Jira Integration + Normalization)

**Assigned stories**: US-B06, US-B07  
**Scope**: Jira client (live env-driven + mock fallback), webhook payload parsing readiness, and typed normalization into internal issue schema.

## 1) Files to create/modify and responsibilities

- [ ] `app/schemas/jira.py`
  - Raw Jira API/webhook-facing schemas for issue fields, comments, attachment metadata, and webhook event envelope.
- [ ] `app/schemas/issue.py`
  - Clean internal normalized issue schema consumed by downstream retrieval/analysis.
- [ ] `app/integrations/jira_client.py`
  - Jira client interface with live/mock modes.
  - `get_issue_bundle(issue_id)` returns issue + comments + attachment metadata.
  - `extract_issue_key_from_webhook(payload)` helper for webhook readiness.
- [ ] `app/services/issue_normalizer.py`
  - Map Jira raw issue + comments into `NormalizedIssue` with typed fields and derived text.
- [ ] `tests/fixtures/jira_issue_rest_sample.json`
  - Deterministic sample Jira issue payload fixture.
- [ ] `tests/fixtures/jira_webhook_sample.json`
  - Deterministic sample webhook payload fixture.
- [ ] `tests/test_jira_client_mock.py`
  - Unit tests for mock fallback behavior and data contract shape.
- [ ] `tests/test_normalize_issue.py`
- [x] `app/schemas/jira.py`
  - Raw Jira API/webhook-facing schemas for issue fields, comments, attachment metadata, and webhook event envelope.
- [x] `app/schemas/issue.py`
  - Clean internal normalized issue schema consumed by downstream retrieval/analysis.
- [x] `app/integrations/jira_client.py`
  - Jira client interface with live/mock modes.
  - `get_issue_bundle(issue_id)` returns issue + comments + attachment metadata.
  - `extract_issue_key_from_webhook(payload)` helper for webhook readiness.
- [x] `app/services/issue_normalizer.py`
  - Map Jira raw issue + comments into `NormalizedIssue` with typed fields and derived text.
- [x] `tests/fixtures/jira_issue_rest_sample.json`
  - Deterministic sample Jira issue payload fixture.
- [x] `tests/fixtures/jira_webhook_sample.json`
  - Deterministic sample webhook payload fixture.
- [x] `tests/test_jira_client_mock.py`
  - Unit tests for mock fallback behavior and data contract shape.
- [x] `tests/test_normalize_issue.py`
  - Unit tests for normalization and webhook key extraction.
  - Unit tests for normalization and webhook key extraction.

## 2) Jira client interface and behavior

- [x] Interface: `JiraClient.get_issue_bundle(issue_id: str) -> JiraIssueBundle`
  - `JiraIssueBundle` includes:
    - raw `issue` object
    - list of `comments`
    - list of `attachments_metadata`
    - `source_mode` (`live` or `mock`)
- [x] Mode selection:
  - **live** when required env vars are present (`JIRA_BASE_URL`, `JIRA_API_TOKEN`, and `JIRA_EMAIL` or `JIRA_USER`)
  - **mock** fallback otherwise (deterministic, no network)
- [x] Live mode responsibilities:
  - GET issue by ID/key from Jira REST API
  - GET comments endpoint
  - parse attachment metadata from issue fields
- [x] Mock mode responsibilities:
  - return deterministic in-memory issue/comment payloads matching schema
  - allow tests to run without network

## 3) Normalization schema design

- [x] Internal schema in `app/schemas/issue.py`:
  - `issue_id`, `issue_key`, `title`, `description`
  - `labels`, `status`, `priority`, `issue_type`
  - `assignee`, `reporter`
  - `service`, `environment` (derived from labels/content when possible)
  - `comments` (normalized text list)
  - `attachments_metadata` (id/filename/mime/size)
  - `derived_text` (concatenated title+description+comments for retrieval)
- [x] Normalizer should:
  - safely flatten Jira description/comment bodies (string or Jira document-like structures)
  - avoid assumptions about missing fields
  - keep output deterministic and easy to test

## 4) Tests to add

- [x] `tests/test_jira_client_mock.py`
  - verifies fallback to mock mode with current default env setup
  - validates bundle has issue/comments/attachments fields
- [x] `tests/test_normalize_issue.py`
  - loads fixture issue payload, normalizes, checks required normalized fields
  - validates `derived_text` includes title/description/comment content
  - validates webhook key extraction helper

## 5) Assumptions and deferred items

Assumptions
- [x] Unit 3 does not call live Jira in tests (mock mode/fixtures only).
- [x] Internal normalized schema should be stable for Unit 4 analysis input.

Deferred (not in Unit 3)
- [ ] Ollama/model integration
- [ ] JSON repair logic
- [ ] SQLite persistence
- [ ] Streamlit UI
- [ ] Additional Jira workflows (posting comments/transitions)

## 6) Execution constraints

- [x] Execute Unit 3 only.
- [x] Keep integration and normalization independently testable.
- [x] Do not begin Unit 4 without explicit user approval.
