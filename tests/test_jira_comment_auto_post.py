from __future__ import annotations

import json
from datetime import datetime, timezone
import pytest
import httpx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api import deps
from app.db.base import Base
from app.main import create_app
from app.schemas.analysis import AnalysisDiagnostics, AnalysisResult
from app.schemas.api import CommentPostResponse
from app.services.analysis_store import AnalysisStore
from app.integrations.jira_client import JiraClient
from app.models.analysis import AnalysisRecord


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return local()


class FakeJiraClient:
    def __init__(self, mode: str = "mock", raise_err: Exception | None = None):
        self.mode = mode
        self.raise_err = raise_err
        self.posted_comments: list[tuple[str, str]] = []

    def add_comment(self, issue_key: str, body: str) -> str | None:
        if self.raise_err:
            raise self.raise_err
        self.posted_comments.append((issue_key, body))
        if self.mode == "live":
            return "live-comment-id-123"
        return "mock-comment-1"


class FakePipeline:
    def __init__(self, jira_client: FakeJiraClient):
        self.jira_client = jira_client


class FakeAnalysisStore:
    def __init__(self, record: AnalysisResult | None = None, is_empty_draft: bool = False):
        self.record = record
        self.is_empty_draft = is_empty_draft

    def get_latest_by_issue(self, issue_id: str):
        if self.record is None:
            return None

        class R:
            id = 1
            issue_id = "KAN-1"
            issue_key = "KAN-1"
            analysis_json = (
                self.record.model_dump_json()
                if not self.is_empty_draft
                else json.dumps({"jira_comment_draft": ""})
            )
            created_at = datetime.now(timezone.utc)

        return R()


def _client_with_overrides(
    *,
    jira_client: FakeJiraClient,
    report_record: AnalysisResult | None = None,
    is_empty_draft: bool = False,
) -> TestClient:
    app = create_app()
    app.dependency_overrides[deps.get_triage_pipeline] = lambda: FakePipeline(jira_client)
    app.dependency_overrides[deps.get_analysis_store] = lambda: FakeAnalysisStore(report_record, is_empty_draft)
    return TestClient(app)


def test_auto_post_mock_mode() -> None:
    # 1. Mock mode returns success, no live Jira HTTP call
    jira_client = FakeJiraClient(mode="mock")
    analysis = AnalysisResult(
        issue_id="KAN-1",
        summary="Triage summary",
        category="infra",
        severity="medium",
        likely_owner_team="Infra Team",
        confidence=0.8,
        jira_comment_draft="Please look at infra.",
    )
    client = _client_with_overrides(jira_client=jira_client, report_record=analysis)
    res = client.post("/issues/KAN-1/comment")
    assert res.status_code == 200
    body = res.json()
    assert body["issue_id"] == "KAN-1"
    assert body["comment_posted"] is True
    assert body["mode"] == "mock"
    assert body["comment_id"] == "mock-comment-1"
    assert len(jira_client.posted_comments) == 1
    assert jira_client.posted_comments[0] == ("KAN-1", "Please look at infra.")


def test_auto_post_live_mode_success() -> None:
    # 2. Mock JiraClient.add_comment success, endpoint returns 200 and comment_posted=True
    jira_client = FakeJiraClient(mode="live")
    analysis = AnalysisResult(
        issue_id="KAN-1",
        summary="Triage summary",
        category="infra",
        severity="medium",
        likely_owner_team="Infra Team",
        confidence=0.8,
        jira_comment_draft="Please look at infra.",
    )
    client = _client_with_overrides(jira_client=jira_client, report_record=analysis)
    res = client.post("/issues/KAN-1/comment")
    assert res.status_code == 200
    body = res.json()
    assert body["issue_id"] == "KAN-1"
    assert body["comment_posted"] is True
    assert body["mode"] == "live"
    assert body["comment_id"] == "live-comment-id-123"


def test_auto_post_no_analysis() -> None:
    # 3. Endpoint returns 400 if no analysis exists
    jira_client = FakeJiraClient(mode="mock")
    client = _client_with_overrides(jira_client=jira_client, report_record=None)
    res = client.post("/issues/KAN-1/comment")
    assert res.status_code == 400
    assert "No analysis exists" in res.json()["detail"]


def test_auto_post_no_draft() -> None:
    # 4. Endpoint returns 400 if jira_comment_draft missing or empty
    jira_client = FakeJiraClient(mode="mock")
    analysis = AnalysisResult(
        issue_id="KAN-1",
        summary="Triage summary",
        category="infra",
        severity="medium",
        likely_owner_team="Infra Team",
        confidence=0.8,
        jira_comment_draft="Please look at infra.",
    )
    client = _client_with_overrides(jira_client=jira_client, report_record=analysis, is_empty_draft=True)
    res = client.post("/issues/KAN-1/comment")
    assert res.status_code == 400
    assert "Jira comment draft is missing, empty, or whitespace-only" in res.json()["detail"]


def test_auto_post_jira_error() -> None:
    # 5. Mock Jira client raising HTTP error, endpoint returns 502/503
    analysis = AnalysisResult(
        issue_id="KAN-1",
        summary="Triage summary",
        category="infra",
        severity="medium",
        likely_owner_team="Infra Team",
        confidence=0.8,
        jira_comment_draft="Please look at infra.",
    )

    # Test 401 Unauthorized -> 502
    req = httpx.Request("POST", "http://jira/comment")
    resp = httpx.Response(401, request=req)
    err_401 = httpx.HTTPStatusError("Auth error", request=req, response=resp)
    jira_client = FakeJiraClient(mode="live", raise_err=err_401)
    client = _client_with_overrides(jira_client=jira_client, report_record=analysis)
    res = client.post("/issues/KAN-1/comment")
    assert res.status_code == 502
    assert "Jira authentication or authorization error" in res.json()["detail"]

    # Test 404 Not Found -> 502
    resp_404 = httpx.Response(404, request=req)
    err_404 = httpx.HTTPStatusError("Not Found", request=req, response=resp_404)
    jira_client = FakeJiraClient(mode="live", raise_err=err_404)
    client = _client_with_overrides(jira_client=jira_client, report_record=analysis)
    res = client.post("/issues/KAN-1/comment")
    assert res.status_code == 502
    assert "Jira issue not found" in res.json()["detail"]

    # Test TimeoutException -> 503
    err_timeout = httpx.TimeoutException("Timeout")
    jira_client = FakeJiraClient(mode="live", raise_err=err_timeout)
    client = _client_with_overrides(jira_client=jira_client, report_record=analysis)
    res = client.post("/issues/KAN-1/comment")
    assert res.status_code == 503
    assert "Jira service timeout or connection error" in res.json()["detail"]


def test_get_latest_by_issue_returns_latest() -> None:
    # 6. Verify store returns newest analysis row for same issue
    db = _session()
    store = AnalysisStore(db)
    analysis1 = AnalysisResult(
        issue_id="10001",
        summary="Auth timeout version 1",
        category="runtime",
        severity="high",
        likely_owner_team="Identity Team",
        confidence=0.71,
        jira_comment_draft="Draft 1",
        created_at=datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone.utc),
    )
    analysis2 = AnalysisResult(
        issue_id="10001",
        summary="Auth timeout version 2",
        category="runtime",
        severity="high",
        likely_owner_team="Identity Team",
        confidence=0.81,
        jira_comment_draft="Draft 2",
        created_at=datetime(2026, 4, 1, 13, 0, 0, tzinfo=timezone.utc),
    )
    store.save_analysis(issue_id="10001", issue_key="BUG-10001", analysis=analysis1)
    store.save_analysis(issue_id="10001", issue_key="BUG-10001", analysis=analysis2)

    latest = store.get_latest_by_issue("10001")
    assert latest is not None
    assert latest.issue_key == "BUG-10001"

    parsed = json.loads(latest.analysis_json)
    assert parsed["summary"] == "Auth timeout version 2"
