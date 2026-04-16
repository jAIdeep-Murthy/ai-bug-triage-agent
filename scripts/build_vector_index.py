"""
Build the ChromaDB vector index from the 500 Eclipse JDT bugs in local data.
Run once after load_real_data.py, and re-run any time the bug dataset
changes.

Usage: python scripts/build_vector_index.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services.dataset_loader import load_synthetic_datasets
from app.services.vector_store import get_vector_store


def build_vector_index() -> None:
    ds = load_synthetic_datasets()
    bugs = ds.historical_bugs

    print(f"Found {len(bugs)} bugs in SQLite. Building vector index...")
    vector_store = get_vector_store()
    vector_store.delete_all()

    payload: list[dict] = []
    for b in bugs:
        payload.append(
            {
                "issue_key": str(b.id or ""),
                "title": str(b.title or ""),
                "description": str(b.summary or ""),
                "severity": str(b.severity or ""),
                "category": str(b.category or ""),
                "owner_team": str(b.team or ""),
            }
        )

    vector_store.upsert_bugs_bulk(payload)
    total = vector_store.count()
    print(f"Vector store count after index: {total}")

    results = vector_store.semantic_search("authentication timeout production", n_results=3)
    print("Semantic sanity-check top 3:")
    for hit in results[:3]:
        print(
            f"  {hit['issue_key']} | similarity={hit['similarity_score']:.3f}"
        )

    print(f"Vector index built successfully. {total} documents indexed.")


if __name__ == "__main__":
    build_vector_index()

