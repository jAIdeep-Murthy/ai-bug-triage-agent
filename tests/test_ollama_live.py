from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.agents.orchestrator import AnalysisOrchestrator
from app.schemas.issue import NormalizedIssue
from app.schemas.retrieval import (
    RetrievalQuery,
    RetrievalResult,
    EvidenceItem,
    RetrievedIncident,
)

pytestmark = pytest.mark.live


def test_live_pipeline_full() -> None:
    issue = NormalizedIssue(
        issue_id="001",
        issue_key="TEST-001",
        title="Login service returns 502 after deploy",
        description="Users cannot log in. Service returns 502. Deploy was 30 min ago.",
        labels=["p1", "backend"],
        status="To Do",
        priority="High",
        issue_type="Bug",
        assignee=None,
        reporter="tester",
        service="auth-service",
        environment="production",
        comments=[],
        attachments_metadata=[],
        derived_text="Login service returns 502 after deploy. Users cannot log in.",
    )

    retrieval = RetrievalResult(
        query=RetrievalQuery(
            text_query="login 502 after deploy",
            service="auth-service",
            environment="production",
            labels=["p1", "backend"],
        ),
        top_k=5,
        created_at=datetime.now(timezone.utc),
        candidates=[
            RetrievedIncident(
                id="BUG-0001",
                score=0.87,
                match_reasons=["Matches 502 after deploy pattern in auth-service"],
                evidence=[
                    EvidenceItem(
                        snippet_type="log",
                        id="log-1",
                        text="Upstream gateway returned 502 shortly after deployment.",
                    )
                ],
            )
        ],
    )

    orch = AnalysisOrchestrator(model_client=None)
    # Avoid demo-mode behavior even if environment is misconfigured; do not touch global cache.
    orch.settings.demo_mode = False
    orch.demo_mode_enabled = False

    result = orch.run(issue, retrieval)

    from app.schemas.analysis import AnalysisResult  # local import to keep test intent explicit

    assert isinstance(result.analysis, AnalysisResult)
    assert result.analysis.issue_id == "TEST-001"
    assert isinstance(result.analysis.category, str) and result.analysis.category
    assert result.analysis.severity in {"low", "medium", "high", "critical"}
    assert 0.0 <= result.analysis.confidence <= 1.0
    assert len(result.analysis.recommended_steps) >= 1
    assert result.diagnostics.model_name == "qwen2.5:7b"
    assert result.diagnostics.raw_response_length > 0
    assert isinstance(result.diagnostics.used_repair, bool)

