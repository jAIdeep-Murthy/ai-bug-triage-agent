"""JSON parse and repair fallback utilities for model outputs."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass


CODE_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", flags=re.IGNORECASE | re.DOTALL)


@dataclass
class RepairResult:
    text: str
    used_repair: bool


def _strip_code_fences(raw: str) -> str:
    match = CODE_FENCE_RE.search(raw)
    if match:
        return match.group(1).strip()
    return raw.strip()


def _extract_outer_json_object(raw: str) -> str:
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return raw
    return raw[start : end + 1]


def _remove_trailing_commas(raw: str) -> str:
    # Remove trailing commas before } or ]
    return re.sub(r",\s*([}\]])", r"\1", raw)


def repair_json_text(raw: str) -> RepairResult:
    """Repair common model formatting issues and return candidate JSON text."""
    cleaned = _strip_code_fences(raw)
    extracted = _extract_outer_json_object(cleaned)
    normalized = _remove_trailing_commas(extracted)
    used_repair = normalized != raw.strip()
    return RepairResult(text=normalized, used_repair=used_repair)


def validate_json_text(raw: str) -> None:
    """Raise if text is not valid JSON."""
    json.loads(raw)

