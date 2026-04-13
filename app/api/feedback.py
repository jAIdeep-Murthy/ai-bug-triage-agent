"""Feedback endpoint (storage-only in MVP)."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.api.deps import get_feedback_store
from app.schemas.api import FeedbackRequest, FeedbackResponse
from app.services.feedback_store import FeedbackStore

router = APIRouter(tags=["feedback"])


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(
    payload: FeedbackRequest,
    store: FeedbackStore = Depends(get_feedback_store),
) -> FeedbackResponse:
    feedback_id = store.save_feedback(
        issue_id=payload.issue_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    return FeedbackResponse(
        feedback_id=feedback_id,
        issue_id=payload.issue_id,
        created_at=datetime.now(timezone.utc),
    )

