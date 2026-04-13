from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.analysis import AnalysisResult


def _base(**kwargs):
    data = {
        "issue_id": "BUG-8",
        "summary": "summary",
        "category": "runtime",
        "severity": "medium",
        "likely_owner_team": "Team A",
        "confidence": 0.8,
        "possible_root_causes": ["x"],
        "evidence": ["y"],
        "similar_issues": ["BUG-1"],
        "recommended_steps": ["step"],
        "missing_information": ["log"],
        "jira_comment_draft": "Likely runtime issue; please verify with logs.",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    data.update(kwargs)
    return data


def test_high_confidence_does_not_force_human_review() -> None:
    result = AnalysisResult.model_validate(_base(confidence=0.9))
    assert result.needs_human_review is False


def test_low_confidence_sets_human_review_and_uncertainty() -> None:
    result = AnalysisResult.model_validate(_base(confidence=0.2))
    assert result.needs_human_review is True
    assert result.uncertainty_note is not None


def test_forbidden_comment_claim_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(
            _base(jira_comment_draft="Issue fixed automatically and auto-closed.")
        )

