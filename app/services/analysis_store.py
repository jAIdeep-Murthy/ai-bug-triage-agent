"""Persistence abstraction for analysis reports."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis import AnalysisRecord
from app.schemas.analysis import AnalysisResult


class AnalysisStore:
    """Repository-like abstraction for analysis persistence."""

    def __init__(self, db: Session):
        self.db = db

    def save_analysis(self, issue_id: str, issue_key: str, analysis: AnalysisResult) -> int:
        record = AnalysisRecord(
            issue_id=issue_id,
            issue_key=issue_key,
            summary=analysis.summary,
            category=analysis.category,
            severity=analysis.severity,
            likely_owner_team=analysis.likely_owner_team,
            confidence=analysis.confidence,
            needs_human_review=analysis.needs_human_review,
            analysis_json=analysis.model_dump_json(),
            created_at=analysis.created_at,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record.id

    def get_latest_by_issue(self, issue_id: str) -> AnalysisRecord | None:
        from sqlalchemy import or_
        stmt = (
            select(AnalysisRecord)
            .where(or_(AnalysisRecord.issue_id == issue_id, AnalysisRecord.issue_key == issue_id))
            .order_by(AnalysisRecord.created_at.desc(), AnalysisRecord.id.desc())
        )
        return self.db.execute(stmt).scalars().first()


