from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api import deps
from app.db.base import Base
from app.main import create_app
from app.models.analysis import AnalysisRecord
from app.models.feedback import FeedbackRecord
from app.schemas.analysis import AnalysisResult
from app.schemas.retrieval import EvidenceItem, RetrievedIncident
from app.services.analysis_store import AnalysisStore
from app.services.feedback_store import FeedbackStore
from app.services.retrieval_scorer import apply_feedback_scores


def _setup_db():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()
    return db, FeedbackStore(db), AnalysisStore(db)


def test_multiplier_boost() -> None:
    db, f_store, a_store = _setup_db()

    # 1. Create a dummy analysis that cited "JDT-100"
    analysis = AnalysisResult(
        issue_id="BUG-1",
        summary="dummy",
        category="runtime",
        severity="high",
        likely_owner_team="team",
        confidence=0.9,
        similar_issues=["JDT-100"],
        jira_comment_draft="draft",
        created_at=datetime.now(timezone.utc),
    )
    a_store.save_analysis(issue_id="BUG-1", issue_key="BUG-1", analysis=analysis)

    # 2. Seed a helpful feedback for BUG-1
    f_store.save_feedback(issue_id="BUG-1", rating="helpful", comment="good")

    # 3. Call get_multipliers_for_keys
    multipliers = f_store.get_multipliers_for_keys(["JDT-100"])
    assert multipliers["JDT-100"] > 1.0


def test_multiplier_penalty() -> None:
    db, f_store, a_store = _setup_db()

    # 1. Create a dummy analysis that cited "JDT-200"
    analysis = AnalysisResult(
        issue_id="BUG-2",
        summary="dummy",
        category="runtime",
        severity="high",
        likely_owner_team="team",
        confidence=0.9,
        similar_issues=["JDT-200"],
        jira_comment_draft="draft",
        created_at=datetime.now(timezone.utc),
    )
    a_store.save_analysis(issue_id="BUG-2", issue_key="BUG-2", analysis=analysis)

    # 2. Seed a not_helpful feedback for BUG-2
    f_store.save_feedback(issue_id="BUG-2", rating="not_helpful", comment="bad")

    # 3. Call get_multipliers_for_keys
    multipliers = f_store.get_multipliers_for_keys(["JDT-200"])
    assert multipliers["JDT-200"] < 1.0


def test_no_feedback_neutral() -> None:
    db, f_store, a_store = _setup_db()
    multipliers = f_store.get_multipliers_for_keys(["JDT-300"])
    assert multipliers["JDT-300"] == 1.0


def test_apply_feedback_scores_reranks() -> None:
    c1 = RetrievedIncident(id="C1", score=10.0, match_reasons=[], evidence=[])
    c2 = RetrievedIncident(id="C2", score=8.0, match_reasons=[], evidence=[])

    # Let's say C2 gets a feedback boost of 1.5, making its score 12.0
    multipliers = {"C1": 1.0, "C2": 1.5}

    sorted_candidates = apply_feedback_scores([c1, c2], multipliers)

    assert sorted_candidates[0].id == "C2"
    assert sorted_candidates[0].score == 12.0
    assert sorted_candidates[1].id == "C1"
    assert sorted_candidates[1].score == 10.0


def test_pipeline_feedback_fallback() -> None:
    from app.services.triage_pipeline import TriagePipeline

    mock_jira = MagicMock()
    mock_retrieval = MagicMock()
    mock_orchestrator = MagicMock()
    mock_analysis_store = MagicMock()

    # We mock the database session
    mock_db = MagicMock()
    mock_analysis_store.db = mock_db

    pipeline = TriagePipeline(
        jira_client=mock_jira,
        retrieval_engine=mock_retrieval,
        orchestrator=mock_orchestrator,
        analysis_store=mock_analysis_store,
    )

    # Mock retrieve to return a fake RetrievalResult
    from app.schemas.retrieval import RetrievalQuery, RetrievalResult
    ret_query = RetrievalQuery(text_query="test query")
    ret_incident = RetrievedIncident(id="JDT-1", score=1.0, match_reasons=[], evidence=[])

    mock_retrieval.retrieve.return_value = RetrievalResult(
        query=ret_query,
        top_k=5,
        created_at=datetime.now(timezone.utc),
        candidates=[ret_incident],
    )

    # Mock jira client to return bundle
    from app.schemas.jira import JiraIssueBundle, JiraIssue, JiraIssueFields
    mock_jira.get_issue_bundle.return_value = JiraIssueBundle(
        issue=JiraIssue(
            id="101",
            key="BUG-101",
            fields=JiraIssueFields(
                summary="test",
                description="test description",
                labels=[],
            ),
        ),
        comments=[],
        attachments_metadata=[],
        source_mode="mock"
    )

    # Mock orchestrator run
    from app.schemas.analysis import AnalysisDiagnostics, AnalysisRunResult
    mock_orchestrator.run.return_value = AnalysisRunResult(
        analysis=AnalysisResult(
            issue_id="BUG-101",
            summary="summary",
            category="runtime",
            severity="high",
            likely_owner_team="team",
            confidence=0.8,
            jira_comment_draft="draft",
            created_at=datetime.now(timezone.utc),
        ),
        diagnostics=AnalysisDiagnostics(model_name="test-model")
    )

    # Mock FeedbackStore.get_multipliers_for_keys to raise an Exception
    with patch("app.services.feedback_store.FeedbackStore.get_multipliers_for_keys", side_effect=ValueError("DB Error")):
        # Ensure it runs without error (calls analyze_issue)
        run_res, rec_id, mode = pipeline.analyze_issue("BUG-101")
        assert run_res.analysis.issue_id == "BUG-101"


def test_feedback_integer_rating() -> None:
    app = create_app()
    # Override feedback store to check save_feedback call
    mock_f_store = MagicMock()
    mock_f_store.save_feedback.return_value = 42
    app.dependency_overrides[deps.get_feedback_store] = lambda: mock_f_store

    client = TestClient(app)
    res = client.post(
        "/feedback",
        json={
            "issue_key": "BUG-10001",
            "rating": 5,
            "comment": "Integer rating test",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["feedback_id"] == 42
    assert body["issue_id"] == "BUG-10001"

    # Confirm save_feedback was called with "helpful" rating string (since 5 maps to helpful)
    mock_f_store.save_feedback.assert_called_once_with(
        issue_id="BUG-10001",
        rating="helpful",
        comment="Integer rating test",
    )


def test_feedback_missing_issue_id() -> None:
    app = create_app()
    client = TestClient(app)
    res = client.post(
        "/feedback",
        json={
            "rating": "helpful",
            "comment": "No ID",
        },
    )
    assert res.status_code == 422
