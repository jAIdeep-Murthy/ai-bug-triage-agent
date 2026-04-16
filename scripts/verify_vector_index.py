from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services.vector_store import get_vector_store


def verify_vector_index() -> None:
    store = get_vector_store()
    count = store.count()
    print(f"Total document count: {count}")

    queries = [
        "login authentication failure",
        "null pointer exception crash",
        "UI rendering performance slow",
    ]

    for q in queries:
        print(f"\nQuery: {q}")
        hits = store.semantic_search(q, n_results=3)
        for hit in hits[:3]:
            snippet = str(hit.get("text", ""))[:80]
            print(
                f"  {hit.get('issue_key')} | {hit.get('similarity_score', 0.0):.3f} | {snippet}"
            )

    if count >= 100:
        print("\nVector index is healthy.")
    else:
        print("\nWARNING: Vector index has fewer than 100 documents.")


if __name__ == "__main__":
    verify_vector_index()

