from __future__ import annotations

import json

import pytest

from app.services.json_repair import repair_json_text, validate_json_text


def test_repair_extracts_outer_object_from_wrapped_text() -> None:
    raw = "Model response:\n```json\n{\"a\": 1,}\n```\nthanks"
    repaired = repair_json_text(raw)
    assert repaired.used_repair is True
    parsed = json.loads(repaired.text)
    assert parsed["a"] == 1


def test_repair_keeps_unrepairable_text_invalid() -> None:
    raw = "no-json-content-here"
    repaired = repair_json_text(raw)
    with pytest.raises(json.JSONDecodeError):
        validate_json_text(repaired.text)

