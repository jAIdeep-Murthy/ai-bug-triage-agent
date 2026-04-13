# Unit 7 - Code Generation Plan (Streamlit Dashboard)

## Scope
- Build functional MVP dashboard in `dashboard/streamlit_app.py`
- Keep backend URL configurable
- No backend logic changes required for this unit

## Files to create/modify
- [x] `requirements.txt` (modify)
  - Add Streamlit dependency.
- [x] `dashboard/streamlit_app.py` (create)
  - Health status section.
  - Analyze Issue panel calling `/issues/{id}/analyze`.
  - Past Analyses section using saved issue IDs and `/issues/{id}/report`.
  - Feedback panel calling `/feedback`.

## UI sections
- [x] Header: project name + short description + backend health indicator
- [x] Analyze Issue panel:
  - Jira issue ID input
  - Analyze button
  - render structured analysis fields
- [x] Past Analyses:
  - list/history of analyzed issue IDs in session state
  - load selected report from backend
- [x] Feedback panel:
  - helpful/not helpful controls
  - optional comment
  - submit to backend

## Backend call mapping
- [x] `GET /health`
- [x] `GET /issues/{issue_id}/analyze`
- [x] `GET /issues/{issue_id}/report`
- [x] `POST /feedback`

## Error-handling requirements
- [x] Friendly backend-offline messages
- [x] User-friendly API error messages
- [x] No raw stack traces

## Constraints
- [x] Clean MVP UI (not over-designed)
- [x] Backend URL configurable in file/env
- [x] No auth required for MVP
