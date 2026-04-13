from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.api import deps
from app.main import create_app
from app.schemas.analysis import AnalysisDiagnostics, AnalysisResult, AnalysisRunResult
from app.services.triage_pipeline import AnalysisExecutionError, IssueFetchError


class FakePipeline:
    def __init__(self, *, should_fail: str | None = None):
        self.should_fail = should_fail

    def analyze_issue(self, issue_id: str):
        if self.should_fail == "fetch":
            raise IssueFetchError("Failed Jira request for issue fetch.")
        if self.should_fail == "analysis":
            raise AnalysisExecutionError("Timed out while waiting for model response.")
        analysis = AnalysisResult(
            issue_id=issue_id,
            summary="Likely runtime timeout in auth",
            category="runtime",
            severity="high",
            likely_owner_team="Identity Team",
            confidence=0.72,
            possible_root_causes=["Upstream timeout"],
            evidence=["BUG-0001 similar"],
            similar_issues=["BUG-0001"],
            recommended_steps=["Inspect upstream dependency latency"],
            missing_information=["Need gateway trace id"],
            jira_comment_draft="Likely runtime issue; please verify upstream metrics.",
            created_at=datetime.now(timezone.utc),
        )
        result = AnalysisRunResult(
            analysis=analysis,
            diagnostics=AnalysisDiagnostics(model_name="fake", raw_response_length=123),
        )
        return result, 1, "mock"


class FakeAnalysisStore:
    def __init__(self, record: AnalysisResult | None = None):
        self.record = record

    def get_latest_by_issue(self, issue_id: str):
        if self.record is None:
            return None

        class R:
            analysis_json = self.record.model_dump_json()

        return R()


class FakeFeedbackStore:
    def save_feedback(self, *, issue_id: str, rating: str, comment: str | None):
        _ = (issue_id, rating, comment)
        return 7


def _client_with_overrides(
    *,
    pipeline: FakePipeline | None = None,
    report_record: AnalysisResult | None = None,
) -> TestClient:
    app = create_app()
    app.dependency_overrides[deps.get_triage_pipeline] = lambda: pipeline or FakePipeline()
    app.dependency_overrides[deps.get_analysis_store] = lambda: FakeAnalysisStore(report_record)
    app.dependency_overrides[deps.get_feedback_store] = lambda: FakeFeedbackStore()
    return TestClient(app)


def test_analyze_route_success() -> None:
    client = _client_with_overrides()
    res = client.get("/issues/BUG-123/analyze")
    assert res.status_code == 200
    body = res.json()
    assert body["issue_id"] == "BUG-123"
    assert body["analysis"]["category"] == "runtime"


def test_report_404_when_missing() -> None:
    client = _client_with_overrides(report_record=None)
    res = client.get("/issues/BUG-123/report")
    assert res.status_code == 404


def test_feedback_validation_and_success() -> None:
    client = _client_with_overrides()
    ok = client.post(
        "/feedback",
        json={
            "issue_id": "BUG-123",
            "rating": "helpful",
            "comment": "Useful",
        },
    )
    assert ok.status_code == 200
    bad = client.post("/feedback", json={"issue_id": "BUG-1", "rating": "wrong"})
    assert bad.status_code == 422


def test_webhook_bad_payload() -> None:
    client = _client_with_overrides()
    res = client.post("/webhooks/jira", json={"payload": {"webhookEvent": "jira:issue_updated"}})
    assert res.status_code == 400


def test_analyze_route_handles_pipeline_errors() -> None:
    client = _client_with_overrides(pipeline=FakePipeline(should_fail="fetch"))
    res = client.get("/issues/BUG-123/analyze")
    assert res.status_code == 502

