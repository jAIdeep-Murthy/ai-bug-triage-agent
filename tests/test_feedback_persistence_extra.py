from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.feedback import FeedbackRecord
from app.services.feedback_store import FeedbackStore


def _store() -> FeedbackStore:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return FeedbackStore(local())


def test_feedback_persists_without_comment() -> None:
    store = _store()
    rec_id = store.save_feedback(issue_id="BUG-22", rating="helpful", comment=None)
    assert rec_id > 0


def test_feedback_multiple_records_are_stored() -> None:
    store = _store()
    first = store.save_feedback(issue_id="BUG-22", rating="helpful", comment="ok")
    second = store.save_feedback(issue_id="BUG-22", rating="not_helpful", comment="bad")
    assert first != second
    rows = store.db.query(FeedbackRecord).all()
    assert len(rows) == 2

