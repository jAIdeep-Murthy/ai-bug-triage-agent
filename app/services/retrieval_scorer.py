from __future__ import annotations

from app.schemas.retrieval import RetrievedIncident


def apply_feedback_scores(
    candidates: list[RetrievedIncident],
    multipliers: dict[str, float],
) -> list[RetrievedIncident]:
    """Adjusts each candidate's score field by its multiplier.
    Sorts by adjusted score descending, then by ID ascending.
    If a candidate's key is not in multipliers, use 1.0.
    """
    for c in candidates:
        mult = multipliers.get(c.id, 1.0)
        c.score = round(c.score * mult, 4)

    return sorted(candidates, key=lambda x: (-x.score, x.id))
