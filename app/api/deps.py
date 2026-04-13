"""FastAPI dependency providers for Unit 5 API wiring."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.services.analysis_store import AnalysisStore
from app.services.dataset_loader import load_synthetic_datasets
from app.services.feedback_store import FeedbackStore
from app.services.triage_pipeline import TriagePipeline


def get_analysis_store(db: Session = Depends(get_db_session)) -> AnalysisStore:
    return AnalysisStore(db)


def get_feedback_store(db: Session = Depends(get_db_session)) -> FeedbackStore:
    return FeedbackStore(db)


@lru_cache
def _cached_datasets():
    return load_synthetic_datasets()


def get_triage_pipeline(
    analysis_store: AnalysisStore = Depends(get_analysis_store),
) -> TriagePipeline:
    return TriagePipeline.from_defaults(datasets=_cached_datasets(), analysis_store=analysis_store)

