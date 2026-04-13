from __future__ import annotations

import os
from typing import Any

import httpx
import streamlit as st


BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000")
HTTP_TIMEOUT_SECONDS = 20.0


def _api_get(path: str) -> tuple[int, dict[str, Any] | str]:
    url = f"{BACKEND_BASE_URL.rstrip('/')}{path}"
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS) as client:
            resp = client.get(url)
        content_type = resp.headers.get("content-type", "")
        if "application/json" in content_type:
            return resp.status_code, resp.json()
        return resp.status_code, resp.text
    except httpx.RequestError:
        return 0, "Backend is unreachable."


def _api_post(path: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any] | str]:
    url = f"{BACKEND_BASE_URL.rstrip('/')}{path}"
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS) as client:
            resp = client.post(url, json=payload)
        content_type = resp.headers.get("content-type", "")
        if "application/json" in content_type:
            return resp.status_code, resp.json()
        return resp.status_code, resp.text
    except httpx.RequestError:
        return 0, "Backend is unreachable."


def _render_health() -> None:
    st.subheader("Backend Health")
    code, body = _api_get("/health")
    if code == 200 and isinstance(body, dict):
        st.success(
            f"Backend online | jira_mode={body.get('jira_mode')} | model={body.get('model_name')}"
        )
    elif code == 0:
        st.warning("Backend offline. Start backend and refresh.")
    else:
        st.warning("Backend health check failed.")


def _render_analysis_result(data: dict[str, Any], *, draft_key: str) -> None:
    analysis = data.get("analysis", {})
    if not isinstance(analysis, dict):
        st.error("Invalid analysis response format.")
        return

    st.subheader("Analysis Result")
    st.write(f"**Summary:** {analysis.get('summary', '-')}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Category", str(analysis.get("category", "-")))
    col2.metric("Severity", str(analysis.get("severity", "-")))

    confidence = float(analysis.get("confidence", 0.0) or 0.0)
    col3.metric("Confidence", f"{confidence:.2f}")
    st.progress(min(max(confidence, 0.0), 1.0))

    st.write(f"**Likely owner team:** {analysis.get('likely_owner_team', '-')}")

    if analysis.get("needs_human_review"):
        st.warning("Needs human review: low confidence or uncertainty flagged.")

    similar = analysis.get("similar_issues", [])
    st.write("**Similar issues:**")
    if similar:
        for item in similar:
            st.markdown(f"- `{item}`")
    else:
        st.markdown("- none")

    steps = analysis.get("recommended_steps", [])
    st.write("**Recommended steps:**")
    if steps:
        for idx, step in enumerate(steps, start=1):
            st.markdown(f"{idx}. {step}")
    else:
        st.markdown("No recommended steps available.")

    missing = analysis.get("missing_information", [])
    st.write("**Missing information:**")
    if missing:
        for item in missing:
            st.markdown(f"- {item}")
    else:
        st.markdown("- none")

    draft = analysis.get("jira_comment_draft", "")
    st.text_area(
        "Jira comment draft (copyable)",
        value=draft,
        height=180,
        key=draft_key,
    )


def _render_analyze_panel() -> None:
    st.subheader("Analyze Issue")
    issue_id = st.text_input(
        "Jira issue ID",
        value="",
        placeholder="e.g., BUG-123",
        key="jira_issue_id_input",
    )
    if st.button(
        "Analyze",
        type="primary",
        use_container_width=True,
        key="analyze_issue_button",
    ):
        if not issue_id.strip():
            st.error("Please enter an issue ID.")
            return
        with st.spinner("Analyzing issue..."):
            code, body = _api_get(f"/issues/{issue_id.strip()}/analyze")
        if code == 200 and isinstance(body, dict):
            st.session_state["current_issue_id"] = issue_id.strip()
            st.session_state["current_analysis_response"] = body
            history = st.session_state.setdefault("history_issue_ids", [])
            if issue_id.strip() not in history:
                history.append(issue_id.strip())
            _render_analysis_result(body, draft_key="jira_draft_analyze")
        elif code in (502, 504) and isinstance(body, dict):
            st.error(f"Analysis failed: {body.get('detail', 'Backend integration error.')}")
        elif code == 0:
            st.error("Backend is offline or unreachable.")
        else:
            detail = body.get("detail") if isinstance(body, dict) else str(body)
            st.error(f"Analyze request failed ({code}): {detail}")

    cached = st.session_state.get("current_analysis_response")
    if isinstance(cached, dict):
        st.divider()
        _render_analysis_result(cached, draft_key="jira_draft_cached")


def _render_past_analyses() -> None:
    st.subheader("Past Analyses")
    history = st.session_state.setdefault("history_issue_ids", [])
    if not history:
        st.info("No analyzed issues yet in this dashboard session.")
        return

    selected = st.selectbox(
        "Select issue",
        options=history,
        index=len(history) - 1,
        key="past_analyses_select_issue",
    )
    if st.button("Load report", use_container_width=True, key="load_report_button"):
        with st.spinner("Loading report..."):
            code, body = _api_get(f"/issues/{selected}/report")
        if code == 200 and isinstance(body, dict):
            wrapped = {"analysis": body.get("analysis", {})}
            st.session_state["current_issue_id"] = selected
            st.session_state["current_analysis_response"] = wrapped
            _render_analysis_result(wrapped, draft_key="jira_draft_report")
        elif code == 404:
            st.warning("No persisted report found for that issue yet.")
        elif code == 0:
            st.error("Backend is offline or unreachable.")
        else:
            detail = body.get("detail") if isinstance(body, dict) else str(body)
            st.error(f"Report request failed ({code}): {detail}")


def _render_feedback_panel() -> None:
    st.subheader("Feedback")
    issue_id = st.session_state.get("current_issue_id")
    if not issue_id:
        st.info("Analyze or load an issue first to submit feedback.")
        return

    rating = st.radio(
        "Was this analysis helpful?",
        options=["helpful", "not_helpful"],
        horizontal=True,
        key="feedback_rating_radio",
    )
    comment = st.text_area(
        "Optional comment",
        value="",
        height=120,
        key="feedback_comment_textarea",
    )
    if st.button("Submit feedback", use_container_width=True, key="submit_feedback_button"):
        payload = {"issue_id": issue_id, "rating": rating, "comment": comment or None}
        code, body = _api_post("/feedback", payload)
        if code == 200 and isinstance(body, dict):
            st.success(f"Feedback saved (id={body.get('feedback_id')}).")
        elif code == 422:
            st.error("Invalid feedback payload. Check required fields.")
        elif code == 0:
            st.error("Backend is offline or unreachable.")
        else:
            detail = body.get("detail") if isinstance(body, dict) else str(body)
            st.error(f"Feedback request failed ({code}): {detail}")


def main() -> None:
    st.set_page_config(page_title="AI Bug Triage Dashboard", layout="wide")
    st.title("AI Bug Triage and Resolution Dashboard")
    st.caption(
        "Local-first dashboard for Jira-driven AI triage reports. Human review remains required."
    )
    st.write(f"Backend URL: `{BACKEND_BASE_URL}`")

    _render_health()
    st.divider()

    left, right = st.columns([2, 1])
    with left:
        _render_analyze_panel()
        st.divider()
        _render_past_analyses()
    with right:
        _render_feedback_panel()


if __name__ == "__main__":
    main()

