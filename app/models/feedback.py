"""ORM model for persisted feedback."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FeedbackRecord(Base):
    __tablename__ = "feedback_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    issue_id: Mapped[str] = mapped_column(String(128), index=True)
    rating: Mapped[str] = mapped_column(String(32))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

