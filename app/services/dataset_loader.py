"""
Load synthetic datasets from committed JSON files under `data/`.

Unit 2 uses keyword + metadata retrieval only. These datasets provide:
- historical bug records
- runbook snippets
- config snippets
- log/error snippets
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class HistoricalBug(BaseModel):
    id: str
    title: str
    summary: str
    service: str
    environment: str
    team: str
    severity: str
    category: str
    error_signature: str
    root_cause: str
    resolution: str
    created_at: datetime
    labels: list[str]
    duplicate_of: str | None = None
    evidence: dict[str, list[str]] = Field(default_factory=dict)


class RunbookSnippet(BaseModel):
    id: str
    service: str
    environment: str
    title: str
    steps: list[str]
    text: str


class ConfigExample(BaseModel):
    id: str
    service: str
    environment: str
    name: str
    text: str


class LogSnippet(BaseModel):
    id: str
    service: str
    environment: str
    error_signature: str
    text: str


@dataclass(frozen=True)
class SyntheticDatasets:
    """In-memory view of the synthetic datasets plus helper indexes."""

    historical_bugs: list[HistoricalBug]
    runbooks: dict[str, RunbookSnippet]
    configs: dict[str, ConfigExample]
    logs: dict[str, LogSnippet]


def _default_data_dir() -> Path:
    """Compute repository root -> data/ path robustly."""
    # app/services/dataset_loader.py -> parents[2] == repo root
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "data"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_synthetic_datasets(data_dir: Path | None = None) -> SyntheticDatasets:
    """Load datasets from `data_dir` (default: repository `data/`)."""

    base = data_dir or _default_data_dir()
    historical_bugs_path = base / "historical_bugs.json"
    runbooks_path = base / "runbooks.json"
    configs_path = base / "configs.json"
    logs_path = base / "logs.json"

    missing: list[str] = []
    for p in [historical_bugs_path, runbooks_path, configs_path, logs_path]:
        if not p.exists():
            missing.append(str(p))
    if missing:
        raise FileNotFoundError(
            "Synthetic dataset files missing; run the generator first. Missing: "
            + ", ".join(missing)
        )

    historical_bugs_raw = _load_json(historical_bugs_path)
    runbooks_raw = _load_json(runbooks_path)
    configs_raw = _load_json(configs_path)
    logs_raw = _load_json(logs_path)

    historical_bugs = [HistoricalBug.model_validate(x) for x in historical_bugs_raw]
    runbooks_list = [RunbookSnippet.model_validate(x) for x in runbooks_raw]
    configs_list = [ConfigExample.model_validate(x) for x in configs_raw]
    logs_list = [LogSnippet.model_validate(x) for x in logs_raw]

    return SyntheticDatasets(
        historical_bugs=historical_bugs,
        runbooks={rb.id: rb for rb in runbooks_list},
        configs={c.id: c for c in configs_list},
        logs={l.id: l for l in logs_list},
    )

