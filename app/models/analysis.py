"""ORM model for persisted analysis reports."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AnalysisRecord(Base):
    __tablename__ = "analysis_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    issue_id: Mapped[str] = mapped_column(String(128), index=True)
    issue_key: Mapped[str] = mapped_column(String(128), index=True)
    summary: Mapped[str] = mapped_column(String(1024))
    category: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(32))
    likely_owner_team: Mapped[str] = mapped_column(String(256))
    confidence: Mapped[float] = mapped_column(Float)
    needs_human_review: Mapped[bool] = mapped_column(Boolean, default=False)
    analysis_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

