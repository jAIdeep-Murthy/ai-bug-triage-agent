from __future__ import annotations

from datetime import datetime, timezone

from app.agents.model_client import ModelResponse
from app.agents.orchestrator import AnalysisOrchestrator
from app.schemas.issue import NormalizedIssue
from app.schemas.retrieval import RetrievalQuery, RetrievalResult


class FakeModelClient:
    def __init__(self, content: str):
        self._content = content

    def generate_json(self, **_: object) -> ModelResponse:
        return ModelResponse(content=self._content, model_name="fake-model")


def _sample_issue() -> NormalizedIssue:
    return NormalizedIssue(
        issue_id="10001",
        issue_key="BUG-10001",
        title="Auth timeout in production",
        description="Login endpoint timing out intermittently.",
        labels=["service:auth", "env:prod"],
        status="To Do",
        priority="High",
        issue_type="Bug",
        assignee=None,
        reporter="monitor",
        service="auth",
        environment="prod",
        comments=[],
        attachments_metadata=[],
        derived_text="Auth timeout in production. Login endpoint timing out intermittently.",
    )


def _sample_retrieval() -> RetrievalResult:
    return RetrievalResult(
        query=RetrievalQuery(text_query="auth timeout prod"),
        top_k=5,
        created_at=datetime.now(timezone.utc),
        candidates=[],
    )


def test_orchestrator_success_path() -> None:
    payload = """
{
  "issue_id": "BUG-10001",
  "summary": "Likely auth runtime timeout",
  "category": "runtime",
  "severity": "high",
  "likely_owner_team": "Identity Team",
  "confidence": 0.72,
  "possible_root_causes": ["Upstream timeout"],
  "evidence": ["No retrieval candidates"],
  "similar_issues": [],
  "recommended_steps": ["Inspect upstream latency"],
  "missing_information": ["Attach request trace id"],
  "jira_comment_draft": "Possible auth timeout; please validate upstream dependency latency.",
  "created_at": "2026-04-08T10:00:00Z"
}
""".strip()
    orch = AnalysisOrchestrator(model_client=FakeModelClient(payload))
    result = orch.run(_sample_issue(), _sample_retrieval())
    assert result.analysis.issue_id == "BUG-10001"
    assert result.diagnostics.used_repair is False


def test_orchestrator_repair_path() -> None:
    malformed = """```json
{
  "issue_id": "BUG-10001",
  "summary": "Likely auth runtime timeout",
  "category": "runtime",
  "severity": "high",
  "likely_owner_team": "Identity Team",
  "confidence": 0.61,
  "possible_root_causes": ["Upstream timeout"],
  "evidence": ["No retrieval candidates"],
  "similar_issues": [],
  "recommended_steps": ["Inspect upstream latency"],
  "missing_information": ["Attach request trace id"],
  "jira_comment_draft": "Likely issue source identified, but human review is required before action.",
  "created_at": "2026-04-08T10:00:00Z",
}
```"""
    orch = AnalysisOrchestrator(model_client=FakeModelClient(malformed))
    result = orch.run(_sample_issue(), _sample_retrieval())
    assert result.diagnostics.used_repair is True
    assert result.analysis.needs_human_review is True

