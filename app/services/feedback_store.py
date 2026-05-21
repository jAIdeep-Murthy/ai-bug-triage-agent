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

    def get_multipliers_for_keys(self, issue_keys: list[str]) -> dict[str, float]:
        import json
        import logging
        from sqlalchemy import select
        from app.models.analysis import AnalysisRecord
        from app.core.config import get_settings

        logger = logging.getLogger(__name__)

        # Default multiplier is 1.0
        multipliers = {key: 1.0 for key in issue_keys}
        if not issue_keys:
            return multipliers

        # Fetch all feedback records and join with analysis records
        try:
            stmt = (
                select(FeedbackRecord.rating, AnalysisRecord.analysis_json)
                .join(AnalysisRecord, FeedbackRecord.issue_id == AnalysisRecord.issue_id)
            )
            rows = self.db.execute(stmt).all()
        except Exception as exc:
            logger.warning("Database query failed in get_multipliers_for_keys: %s", exc)
            return multipliers

        # Group ratings by cited similar_issue key
        key_ratings: dict[str, list[float]] = {key: [] for key in issue_keys}

        rating_map = {
            "helpful": 1.0,
            "partially_helpful": 0.0,
            "not_helpful": -1.0,
        }

        for rating_str, analysis_json in rows:
            if not analysis_json:
                logger.debug("AnalysisRecord.analysis_json is missing or null.")
                continue

            try:
                analysis_data = json.loads(analysis_json)
                similar_issues = analysis_data.get("similar_issues") or []
            except Exception as exc:
                logger.debug("Failed to parse analysis_json: %s", exc)
                continue

            # Map the feedback rating string to float
            val = rating_map.get(rating_str)
            if val is None:
                try:
                    val_num = float(rating_str)
                    if val_num >= 5.0:
                        val = 1.0
                    elif val_num <= 1.0:
                        val = -1.0
                    else:
                        val = (val_num - 3.0) / 2.0
                except ValueError:
                    val = 0.0

            for sim_key in similar_issues:
                if sim_key in key_ratings:
                    key_ratings[sim_key].append(val)

        # Calculate multiplier for each key
        settings = get_settings()
        boost_factor = getattr(settings, "feedback_boost_factor", 0.3)

        for key, ratings in key_ratings.items():
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                avg_rating = max(-1.0, min(1.0, avg_rating))
                multipliers[key] = round(1.0 + (avg_rating * boost_factor), 4)

        return multipliers

