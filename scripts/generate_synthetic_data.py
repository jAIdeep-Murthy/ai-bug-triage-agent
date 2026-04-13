"""
Seeded synthetic dataset generator for the AI Bug Triage demo.

This script is deterministic (fixed seed) and writes committed-ready JSON files
under the repository `data/` directory.

Datasets:
- data/historical_bugs.json
- data/runbooks.json
- data/configs.json
- data/logs.json
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SEED: int = 1337
BASE_DT: datetime = datetime(2025, 1, 1, tzinfo=timezone.utc)


SERVICES: list[str] = [
    "auth",
    "payments",
    "notifications",
    "search",
    "frontend",
    "billing",
]

ENVIRONMENTS: list[str] = ["dev", "staging", "prod"]

TEAMS: list[str] = [
    "Platform Security",
    "Identity Team",
    "Payments Core",
    "Notifications Team",
    "Search Relevance",
    "Frontend Systems",
    "SRE",
]

CATEGORIES: list[str] = [
    "config",
    "runtime",
    "OS mismatch",
    "dependency",
    "infra",
    "deployment regression",
    "code defect",
    "duplicate",
    "insufficient info",
]

SEVERITIES: list[str] = ["low", "medium", "high"]


@dataclass(frozen=True)
class BugTemplate:
    category: str
    service: str
    severity: str
    error_signature: str
    root_cause: str
    resolution: str
    labels: list[str]


BUG_TEMPLATES: list[BugTemplate] = [
    BugTemplate(
        category="runtime",
        service="auth",
        severity="high",
        error_signature="TimeoutError: upstream request timed out while fetching token claims",
        root_cause="Auth service experienced upstream latency and did not apply a longer timeout for token introspection.",
        resolution="Increase upstream timeout for token introspection and add a circuit breaker for repeated timeouts.",
        labels=["error:timeout", "feature:token-introspection", "component:auth"],
    ),
    BugTemplate(
        category="config",
        service="payments",
        severity="high",
        error_signature="ConfigError: missing webhook secret for payment status updates",
        root_cause="Webhook secret rotated but environment configuration was not updated in staging.",
        resolution="Update webhook secret in staging and add configuration validation at startup.",
        labels=["error:config", "component:payments", "feature:webhooks"],
    ),
    BugTemplate(
        category="dependency",
        service="search",
        severity="medium",
        error_signature="DependencyError: Elasticsearch client authentication failed (401)",
        root_cause="TLS settings changed and the client library began requiring an updated CA bundle.",
        resolution="Refresh CA bundle and pin compatible client version for the search cluster.",
        labels=["error:401", "component:search", "dependency:es-client"],
    ),
    BugTemplate(
        category="deployment regression",
        service="notifications",
        severity="medium",
        error_signature="DeploymentError: notification scheduler missed due to clock skew detected",
        root_cause="Node time drift caused scheduled jobs to be skipped after deployment.",
        resolution="Enable NTP enforcement and add job rescheduling when clock skew exceeds threshold.",
        labels=["error:clock-skew", "component:notifications", "type:scheduler"],
    ),
    BugTemplate(
        category="code defect",
        service="frontend",
        severity="high",
        error_signature="TypeError: Cannot read properties of undefined (reading 'status') in failure handler",
        root_cause="Frontend failure handler assumed a response body shape that changed for 5xx errors.",
        resolution="Harden response parsing and add unit tests for error response variants.",
        labels=["error:typeerror", "component:frontend", "path:failure-handler"],
    ),
    BugTemplate(
        category="infra",
        service="billing",
        severity="high",
        error_signature="InfraError: database connection pool exhausted during peak load",
        root_cause="Connection pool max size was too low after increased traffic.",
        resolution="Tune pool sizes and add backpressure; verify with load tests.",
        labels=["error:pool-exhausted", "component:db", "type:load"],
    ),
]


def _tokens(text: str) -> list[str]:
    """Very small tokenization helper for generator labeling."""
    out: list[str] = []
    current = []
    for ch in text.lower():
        if ch.isalnum():
            current.append(ch)
        else:
            if current:
                out.append("".join(current))
                current = []
    if current:
        out.append("".join(current))
    return [t for t in out if len(t) >= 2]


def _stable_id(prefix: str, idx: int) -> str:
    return f"{prefix}-{idx:04d}"


def _json_dump(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def generate() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(SEED)

    # Generate snippets first so bug evidence can reference them.
    runbooks: list[dict[str, Any]] = []
    configs: list[dict[str, Any]] = []
    logs: list[dict[str, Any]] = []

    for i in range(1, 21):
        service = rng.choice(SERVICES)
        env = rng.choice(ENVIRONMENTS)
        runbook_id = _stable_id("RB", i)
        title = f"Runbook {runbook_id}: Diagnose {service} issues in {env}"
        steps = [
            "Check recent deploys and config diffs.",
            "Verify environment variables and feature flags.",
            "Collect failing request traces and relevant logs.",
            "Apply targeted mitigation and confirm recovery.",
        ]
        snippet = (
            f"{title}\n"
            f"Environment: {env}\n"
            f"Service: {service}\n\n"
            f"Common signals:\n"
            f"- Look for error signatures: {rng.choice([t.error_signature for t in BUG_TEMPLATES])}\n"
            f"- Verify service dependencies and timeouts.\n\n"
            f"Suggested steps:\n"
            + "\n".join([f"{k+1}. {s}" for k, s in enumerate(steps)])
        )
        runbooks.append(
            {
                "id": runbook_id,
                "service": service,
                "environment": env,
                "title": title,
                "steps": steps,
                "text": snippet,
            }
        )

    for i in range(1, 16):
        service = rng.choice(SERVICES)
        env = rng.choice(ENVIRONMENTS)
        config_id = _stable_id("CFG", i)
        name = f"{service}.yaml"
        snippet = (
            f"# {config_id} synthetic config example\n"
            f"service: {service}\n"
            f"environment: {env}\n"
            f"timeout_ms: {rng.randint(500, 8000)}\n"
            f"retry_policy: {rng.choice(['exponential', 'fixed'])}\n"
            f"pool_max: {rng.randint(5, 50)}\n"
            f"feature_flags:\n"
            f"  use_new_flow: {rng.choice(['true', 'false'])}\n"
            f"validation:\n"
            f"  fail_on_missing_secrets: true\n"
        )
        configs.append(
            {
                "id": config_id,
                "service": service,
                "environment": env,
                "name": name,
                "text": snippet,
            }
        )

    for i in range(1, 16):
        service = rng.choice(SERVICES)
        env = rng.choice(ENVIRONMENTS)
        log_id = _stable_id("LOG", i)
        template = rng.choice(BUG_TEMPLATES)
        ts = (BASE_DT + timedelta(days=i)).isoformat().replace("+00:00", "Z")
        text = (
            f"{ts} {env.upper()} {service} ERROR {log_id}: {template.error_signature}\n"
            f"trace_id={rng.randint(10**12, 10**13-1)}\n"
            f"context={{\"service\":\"{service}\",\"env\":\"{env}\",\"category\":\"{template.category}\"}}\n"
        )
        logs.append(
            {
                "id": log_id,
                "service": service,
                "environment": env,
                "error_signature": template.error_signature,
                "text": text,
            }
        )

    # Historical bugs.
    historical_bugs: list[dict[str, Any]] = []
    labels_pool: list[str] = [
        "bug:triage-mvp",
        "ui:regression",
        "api:timeout",
        "api:500",
        "queue:scheduler",
        "db:pool",
        "tls:ca-bundle",
        "secret:missing",
        "dependency:auth",
    ]

    for i in range(1, 121):
        tpl = BUG_TEMPLATES[(i - 1) % len(BUG_TEMPLATES)]

        # Vary fields deterministically using rng.
        service = tpl.service if rng.random() < 0.8 else rng.choice(SERVICES)
        env = rng.choice(ENVIRONMENTS)
        team = rng.choice(TEAMS)
        severity = tpl.severity if rng.random() < 0.8 else rng.choice(SEVERITIES)
        category = tpl.category if rng.random() < 0.8 else rng.choice(CATEGORIES)

        bug_id = _stable_id("BUG", i)
        created_at = (BASE_DT + timedelta(days=i)).isoformat().replace("+00:00", "Z")

        # Make the signature mostly deterministic but allow slight variation for realism.
        signature_bits = _tokens(tpl.error_signature)
        unique_tag = signature_bits[rng.randint(0, len(signature_bits) - 1)] if signature_bits else "signature"
        error_signature = f"{tpl.error_signature} [{unique_tag}]"

        title = f"{service}: {category} failure observed in {env}"
        summary = (
            f"Incident {bug_id} in {service} ({env}) failed with error signature: {error_signature}. "
            f"Observed symptoms triggered automated alerts and manual triage."
        )

        # Evidence: pick a small set of snippet IDs.
        rb_ids = rng.sample([r["id"] for r in runbooks], k=rng.randint(1, 2))
        cfg_ids = rng.sample([c["id"] for c in configs], k=rng.randint(0, 1))
        log_ids = rng.sample([l["id"] for l in logs], k=rng.randint(1, 2))

        label_list = list({*tpl.labels, *rng.sample(labels_pool, k=3)})
        label_list = sorted(label_list)

        duplicate_of: str | None = None
        if category == "duplicate" and i > 3:
            # Duplicate references the prior bug deterministically.
            duplicate_of = _stable_id("BUG", i - 3)

        root_cause = tpl.root_cause
        resolution = tpl.resolution

        historical_bugs.append(
            {
                "id": bug_id,
                "title": title,
                "summary": summary,
                "service": service,
                "environment": env,
                "team": team,
                "severity": severity,
                "category": category,
                "error_signature": error_signature,
                "root_cause": root_cause,
                "resolution": resolution,
                "created_at": created_at,
                "labels": label_list,
                "duplicate_of": duplicate_of,
                "evidence": {
                    "runbook_ids": rb_ids,
                    "config_ids": cfg_ids,
                    "log_ids": log_ids,
                },
            }
        )

    # Stable ordering (helps tests and diffs).
    runbooks = sorted(runbooks, key=lambda x: x["id"])
    configs = sorted(configs, key=lambda x: x["id"])
    logs = sorted(logs, key=lambda x: x["id"])
    historical_bugs = sorted(historical_bugs, key=lambda x: x["id"])

    _json_dump(data_dir / "runbooks.json", runbooks)
    _json_dump(data_dir / "configs.json", configs)
    _json_dump(data_dir / "logs.json", logs)
    _json_dump(data_dir / "historical_bugs.json", historical_bugs)


if __name__ == "__main__":
    generate()

