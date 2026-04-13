from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.analysis import AnalysisRecord
from app.models.feedback import FeedbackRecord
from app.schemas.analysis import AnalysisResult
from app.services.analysis_store import AnalysisStore
from app.services.feedback_store import FeedbackStore


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return local()


def test_analysis_store_roundtrip() -> None:
    db = _session()
    store = AnalysisStore(db)
    analysis = AnalysisResult(
        issue_id="10001",
        summary="Auth timeout likely due to upstream latency",
        category="runtime",
        severity="high",
        likely_owner_team="Identity Team",
        confidence=0.71,
        possible_root_causes=["Upstream timeout"],
        evidence=["BUG-0001 similar"],
        similar_issues=["BUG-0001"],
        recommended_steps=["Check upstream health"],
        missing_information=["Need trace id"],
        jira_comment_draft="Likely runtime issue; please validate with traces.",
        created_at=datetime.now(timezone.utc),
    )
    rec_id = store.save_analysis(issue_id="10001", issue_key="BUG-10001", analysis=analysis)
    assert rec_id > 0

    latest = store.get_latest_by_issue("10001")
    assert latest is not None
    assert latest.issue_key == "BUG-10001"
    assert latest.category == "runtime"


def test_feedback_store_roundtrip() -> None:
    db = _session()
    store = FeedbackStore(db)
    feedback_id = store.save_feedback(
        issue_id="10001",
        rating="helpful",
        comment="Good initial triage",
    )
    assert feedback_id > 0
    saved = db.query(FeedbackRecord).filter(FeedbackRecord.id == feedback_id).first()
    assert saved is not None
    assert saved.rating == "helpful"

