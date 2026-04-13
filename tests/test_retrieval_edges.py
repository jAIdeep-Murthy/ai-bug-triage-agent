from __future__ import annotations

from datetime import datetime, timezone

from app.retrieval.keyword_retrieval import KeywordRetrievalEngine
from app.schemas.retrieval import RetrievalQuery
from app.services.dataset_loader import HistoricalBug, SyntheticDatasets


def _dt(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _edge_dataset() -> SyntheticDatasets:
    bugs = [
        HistoricalBug(
            id="BUG-A",
            title="Auth timeout observed",
            summary="Timeout in auth flow",
            service="auth",
            environment="prod",
            team="Identity Team",
            severity="high",
            category="runtime",
            error_signature="TimeoutError auth",
            root_cause="upstream latency",
            resolution="increase timeout",
            created_at=_dt("2026-01-02T00:00:00Z"),
            labels=["service:auth", "env:prod"],
            evidence={},
        ),
        HistoricalBug(
            id="BUG-B",
            title="Auth timeout observed",
            summary="Timeout in auth flow",
            service="auth",
            environment="prod",
            team="Identity Team",
            severity="high",
            category="runtime",
            error_signature="TimeoutError auth",
            root_cause="upstream latency",
            resolution="increase timeout",
            created_at=_dt("2026-01-03T00:00:00Z"),
            labels=["service:auth", "env:prod"],
            evidence={},
        ),
    ]
    return SyntheticDatasets(historical_bugs=bugs, runbooks={}, configs={}, logs={})


def test_partial_match_returns_candidates() -> None:
    engine = KeywordRetrievalEngine(_edge_dataset())
    result = engine.retrieve(RetrievalQuery(text_query="timeout auth"), top_k=5)
    assert len(result.candidates) >= 1


def test_no_match_returns_empty_candidates_edge_dataset() -> None:
    engine = KeywordRetrievalEngine(_edge_dataset())
    result = engine.retrieve(RetrievalQuery(text_query="zzqxywv_not_present"), top_k=5)
    assert result.candidates == []


def test_score_tie_breaking_prefers_newer_created_at() -> None:
    engine = KeywordRetrievalEngine(_edge_dataset())
    result = engine.retrieve(RetrievalQuery(text_query="timeout auth"), top_k=2)
    assert len(result.candidates) == 2
    # Same text/metadata score -> newer created_at (BUG-B) should come first.
    assert result.candidates[0].id == "BUG-B"
    assert result.candidates[1].id == "BUG-A"

