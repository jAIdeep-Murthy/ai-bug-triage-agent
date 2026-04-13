from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.analysis import AnalysisResult
from app.services.json_repair import repair_json_text


def _valid_payload() -> str:
    ts = datetime.now(timezone.utc).isoformat()
    return f"""
{{
  "issue_id": "BUG-321",
  "summary": "Intermittent auth timeout in production",
  "category": "runtime",
  "severity": "high",
  "likely_owner_team": "Identity Team",
  "confidence": 0.58,
  "possible_root_causes": ["Upstream introspection latency"],
  "evidence": ["BUG-0111: similar timeout in auth"],
  "similar_issues": ["BUG-0111"],
  "recommended_steps": ["Check upstream latency", "Verify timeout settings"],
  "missing_information": ["Attach gateway trace IDs"],
  "jira_comment_draft": "Likely auth runtime issue; human review needed before action.",
  "created_at": "{ts}"
}}
""".strip()


def test_analysis_schema_valid_json() -> None:
    parsed = AnalysisResult.model_validate_json(_valid_payload())
    assert parsed.issue_id == "BUG-321"
    assert parsed.needs_human_review is True
    assert parsed.uncertainty_note is not None


def test_json_repair_code_fence_and_trailing_comma() -> None:
    malformed = "```json\n" + _valid_payload().replace("\n}", ",\n}") + "\n```"
    repaired = repair_json_text(malformed)
    assert repaired.used_repair is True
    parsed = AnalysisResult.model_validate_json(repaired.text)
    assert parsed.issue_id == "BUG-321"


def test_analysis_schema_rejects_fixed_claim() -> None:
    payload = _valid_payload().replace(
        "human review needed before action.",
        "issue fixed automatically.",
    )
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate_json(payload)

