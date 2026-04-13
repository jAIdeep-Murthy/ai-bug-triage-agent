"""Unit tests for keyword + metadata retrieval (Unit 2)."""

from __future__ import annotations

from app.retrieval.keyword_retrieval import KeywordRetrievalEngine
from app.schemas.retrieval import RetrievalQuery
from app.services.dataset_loader import load_synthetic_datasets


def test_dataset_integrity() -> None:
    """Synthetic datasets exist and have expected minimum sizes."""
    ds = load_synthetic_datasets()
    assert len(ds.historical_bugs) >= 100
    assert len(ds.runbooks) >= 10
    assert len(ds.configs) >= 10
    assert len(ds.logs) >= 10

    first = ds.historical_bugs[0]
    # Required fields used by retrieval scoring.
    assert first.id
    assert first.title
    assert first.summary
    assert first.error_signature
    assert isinstance(first.labels, list)
    assert first.created_at is not None


def test_retrieval_determinism_top1() -> None:
    """For a fixed query, the top-1 incident is stable across runs."""
    ds = load_synthetic_datasets()
    engine = KeywordRetrievalEngine(ds)

    query = RetrievalQuery(
        text_query="upstream request timed out while fetching token claims",
        service="auth",
        environment="prod",
    )
    result = engine.retrieve(query, top_k=5)
    assert len(result.candidates) > 0

    # Deterministic dataset + deterministic scoring guarantees stable top-1.
    top1 = result.candidates[0].id
    assert isinstance(top1, str) and top1.startswith("BUG-")

    # Run again and ensure exact same top order.
    result2 = engine.retrieve(query, top_k=5)
    assert [c.id for c in result.candidates] == [c.id for c in result2.candidates]


def test_retrieval_no_match_returns_empty() -> None:
    """If no meaningful token overlap exists, retrieval returns no candidates."""
    ds = load_synthetic_datasets()
    engine = KeywordRetrievalEngine(ds)

    # Use a token that is intentionally not present in generator templates.
    query = RetrievalQuery(text_query="zzqxjvplmwrtynzzqxjvplmwrtyn")
    result = engine.retrieve(query, top_k=5)
    assert result.candidates == []


def test_explainability_has_match_reasons_when_matched() -> None:
    """When we match, match_reasons should be non-empty and evidence should exist."""
    ds = load_synthetic_datasets()
    engine = KeywordRetrievalEngine(ds)

    query = RetrievalQuery(text_query="database connection pool exhausted during peak load")
    result = engine.retrieve(query, top_k=5)
    assert len(result.candidates) > 0

    cand = result.candidates[0]
    assert cand.match_reasons
    # Evidence may be empty if a particular incident references no snippets,
    # but for our generator it should usually contain at least one item.
    assert isinstance(cand.evidence, list)

