"""
Retrieval backend interface (extensibility hook).

Unit 2 MVP uses a keyword retrieval backend, but downstream analysis should depend
on a stable contract so we can add semantic retrieval later.
"""

from __future__ import annotations

from typing import Protocol

from app.schemas.retrieval import RetrievalQuery, RetrievalResult


class RetrievalBackend(Protocol):
    """Contract for any retrieval engine."""

    def retrieve(self, query: RetrievalQuery, top_k: int = 5) -> RetrievalResult:
        """Return top-k retrieval candidates and evidence."""

