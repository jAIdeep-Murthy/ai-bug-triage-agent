"""Persistence abstraction for feedback storage."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.feedback import FeedbackRecord


class FeedbackStore:
    def __init__(self, db: Session):
        self.db = db

    def save_feedback(self, *, issue_id: str, rating: str, comment: str | None) -> int:
        rec = FeedbackRecord(issue_id=issue_id, rating=rating, comment=comment)
        self.db.add(rec)
        self.db.commit()
        self.db.refresh(rec)
        return rec.id

