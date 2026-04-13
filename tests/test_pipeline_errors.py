from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.api import deps
from app.main import create_app
from app.schemas.analysis import AnalysisDiagnostics, AnalysisResult, AnalysisRunResult
from app.services.triage_pipeline import AnalysisExecutionError, IssueFetchError


class FakePipeline:
    def __init__(self, mode: str = "ok"):
        self.mode = mode

    def analyze_issue(self, issue_id: str):
        if self.mode == "jira_502":
            raise IssueFetchError("Failed Jira request for issue fetch.")
        if self.mode == "model_504":
            raise AnalysisExecutionError("Timed out while waiting for model response.")
        analysis = AnalysisResult(
            issue_id=issue_id,
            summary="runtime issue",
            category="runtime",
            severity="medium",
            likely_owner_team="Identity Team",
            confidence=0.7,
            possible_root_causes=["upstream latency"],
            evidence=["BUG-0010"],
            similar_issues=["BUG-0010"],
            recommended_steps=["collect traces"],
            missing_information=["full stack trace"],
            jira_comment_draft="Likely runtime issue; please verify with traces.",
            created_at=datetime.now(timezone.utc),
        )
        return (
            AnalysisRunResult(
                analysis=analysis,
                diagnostics=AnalysisDiagnostics(model_name="fake", raw_response_length=5),
            ),
            1,
            "mock",
        )


class MissingStore:
    def get_latest_by_issue(self, issue_id: str):
        _ = issue_id
        return None


class FeedbackStore:
    def save_feedback(self, *, issue_id: str, rating: str, comment: str | None):
        _ = (issue_id, rating, comment)
        return 1


def _client(mode: str) -> TestClient:
    app = create_app()
    app.dependency_overrides[deps.get_triage_pipeline] = lambda: FakePipeline(mode=mode)
    app.dependency_overrides[deps.get_analysis_store] = lambda: MissingStore()
    app.dependency_overrides[deps.get_feedback_store] = lambda: FeedbackStore()
    return TestClient(app)


def test_api_maps_jira_fetch_error_to_502() -> None:
    client = _client("jira_502")
    resp = client.get("/issues/BUG-1/analyze")
    assert resp.status_code == 502


def test_api_maps_model_timeout_to_504() -> None:
    client = _client("model_504")
    resp = client.get("/issues/BUG-1/analyze")
    assert resp.status_code == 504


def test_report_missing_issue_returns_404() -> None:
    client = _client("ok")
    resp = client.get("/issues/BUG-MISSING/report")
    assert resp.status_code == 404

