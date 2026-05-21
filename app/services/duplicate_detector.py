"""Service for detecting likely duplicate issues using vector search."""

from __future__ import annotations

import logging

from app.core.config import get_settings
from app.schemas.api import DuplicateCandidate, DuplicateCheckResult
from app.schemas.issue import NormalizedIssue
from app.services.vector_store import get_vector_store

logger = logging.getLogger(__name__)

def check_duplicate(
    normalized_issue: NormalizedIssue,
    threshold: float | None = None
) -> DuplicateCheckResult:
    """Check if a given issue is a duplicate of historical bugs using semantic similarity."""
    if threshold is None:
        settings = get_settings()
        threshold = settings.duplicate_similarity_threshold

    query_text = f"{normalized_issue.title} {normalized_issue.description}".strip()[:512]
    
    try:
        vector_store = get_vector_store()
        if vector_store.count() == 0:
            return DuplicateCheckResult(
                issue_key=normalized_issue.issue_key,
                is_likely_duplicate=False,
                primary_duplicate_key=None,
                candidates=[],
            )
            
        hits = vector_store.semantic_search(query_text=query_text, n_results=5)
    except Exception as exc:
        logger.warning("Vector search failed during duplicate detection: %s", exc)
        return DuplicateCheckResult(
            issue_key=normalized_issue.issue_key,
            is_likely_duplicate=False,
            primary_duplicate_key=None,
            candidates=[],
        )

    candidates: list[DuplicateCandidate] = []
    
    for hit in hits:
        hit_key = str(hit.get("issue_key") or "")
        score = float(hit.get("similarity_score") or 0.0)
        
        if hit_key and hit_key != normalized_issue.issue_key and score >= threshold:
            candidates.append(DuplicateCandidate(issue_key=hit_key, similarity_score=score))
            
    # Sort just to be safe, though chroma typically orders by distance (highest sim first)
    candidates.sort(key=lambda c: c.similarity_score, reverse=True)
    
    is_likely_duplicate = len(candidates) > 0
    primary_key = candidates[0].issue_key if is_likely_duplicate else None
    
    return DuplicateCheckResult(
        issue_key=normalized_issue.issue_key,
        is_likely_duplicate=is_likely_duplicate,
        primary_duplicate_key=primary_key,
        candidates=candidates,
    )
