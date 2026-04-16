from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.services.vector_store import VectorStore


def _make_store(monkeypatch: pytest.MonkeyPatch, query_payload: dict | None = None, count: int = 3):
    import app.services.vector_store as vs

    fake_collection = MagicMock()
    fake_collection.count.return_value = count
    if query_payload is None:
        query_payload = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }
    fake_collection.query.return_value = query_payload
    fake_collection.get.return_value = {"ids": []}

    fake_client = MagicMock()
    fake_client.get_or_create_collection.return_value = fake_collection

    monkeypatch.setattr(vs.chromadb, "PersistentClient", lambda path: fake_client)
    monkeypatch.setattr(vs, "SentenceTransformerEmbeddingFunction", lambda **kwargs: object())

    store = VectorStore(db_path="data/chroma_db_test")
    return store, fake_collection


def test_upsert_and_count(monkeypatch: pytest.MonkeyPatch) -> None:
    store, _ = _make_store(monkeypatch, count=3)
    assert store.count() == 3


def test_semantic_search_returns_list(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "ids": [["BUG-JDT-001", "BUG-JDT-002"]],
        "documents": [["auth timeout", "null pointer crash"]],
        "metadatas": [[{"severity": "high"}, {"severity": "medium"}]],
        "distances": [[0.15, 0.42]],
    }
    store, _ = _make_store(monkeypatch, query_payload=payload, count=2)
    out = store.semantic_search("auth")
    assert isinstance(out, list)
    assert len(out) == 2
    assert out[0]["similarity_score"] == pytest.approx(0.85)
    assert out[0]["issue_key"] == "BUG-JDT-001"


def test_semantic_search_empty_collection(monkeypatch: pytest.MonkeyPatch) -> None:
    store, coll = _make_store(monkeypatch, count=0)
    out = store.semantic_search("anything")
    assert out == []
    coll.query.assert_not_called()


def test_upsert_replaces_none_with_empty_string(monkeypatch: pytest.MonkeyPatch) -> None:
    store, coll = _make_store(monkeypatch, count=1)
    store.upsert_bug(
        issue_key="BUG-1",
        text="title description",
        metadata={"severity": "high", "category": "runtime", "owner_team": None},
    )
    kwargs = coll.upsert.call_args.kwargs
    assert kwargs["metadatas"][0]["owner_team"] == ""


def test_similarity_score_capped_at_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "ids": [["BUG-JDT-001"]],
        "documents": [["auth timeout"]],
        "metadatas": [[{"severity": "high"}]],
        "distances": [[1.9]],
    }
    store, _ = _make_store(monkeypatch, query_payload=payload, count=1)
    out = store.semantic_search("auth")
    assert out[0]["similarity_score"] >= 0.0


def test_bulk_upsert_batches(monkeypatch: pytest.MonkeyPatch) -> None:
    store, coll = _make_store(monkeypatch, count=1)
    bugs = [
        {
            "issue_key": f"BUG-{i}",
            "title": "title",
            "description": "desc",
            "severity": "medium",
            "category": "runtime",
            "owner_team": "team",
        }
        for i in range(250)
    ]
    store.upsert_bugs_bulk(bugs)
    assert coll.upsert.call_count >= 3

