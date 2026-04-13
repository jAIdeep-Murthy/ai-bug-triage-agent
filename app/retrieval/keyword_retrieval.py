"""
Keyword + metadata retrieval over synthetic datasets.

Unit 2 MVP: retrieval uses only token overlap and metadata filters (no vector DB).
Design goal: keep an interface-compatible contract so future semantic retrieval
can swap in without changing downstream analysis inputs.
"""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Iterable
from app.schemas.retrieval import (
    EvidenceItem,
    RetrievedIncident,
    RetrievalQuery,
    RetrievalResult,
)
from app.services.dataset_loader import SyntheticDatasets


TOKEN_SPLIT_RE = re.compile(r"[^a-zA-Z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase tokenization for explainable keyword retrieval."""
    if not text:
        return []
    parts = [p for p in TOKEN_SPLIT_RE.split(text.lower()) if p]
    return [p for p in parts if len(p) >= 2]


def _overlap_size(a: Iterable[str], b: Iterable[str]) -> int:
    sa = set(a)
    sb = set(b)
    return len(sa & sb)


class KeywordRetrievalEngine:
    """Extensible retrieval engine using keyword overlap only."""

    def __init__(self, datasets: SyntheticDatasets):
        self._datasets = datasets

    def retrieve(self, query: RetrievalQuery, top_k: int = 5) -> RetrievalResult:
        """Retrieve the top-N most similar historical incidents."""
        query_tokens_text = tokenize(query.text_query)
        query_error_tokens = tokenize(" ".join(query.error_signature_tokens or []))
        candidate_filters = {
            "service": query.service,
            "environment": query.environment,
            "labels": query.labels or [],
        }

        ranked: list[tuple[float, str, datetime, list[str], list[EvidenceItem]]] = []

        for bug in self._datasets.historical_bugs:
            match_reasons: list[str] = []

            candidate_error_tokens = tokenize(bug.error_signature)
            candidate_text = " ".join(
                [
                    bug.title,
                    bug.summary,
                    bug.error_signature,
                    bug.category,
                    bug.service,
                    bug.environment,
                    " ".join(bug.labels),
                ]
            )
            candidate_text_tokens = tokenize(candidate_text)

            # Term overlap (general).
            term_overlap_count = _overlap_size(query_tokens_text, candidate_text_tokens)
            term_overlap_score = 0.0
            if term_overlap_count > 0:
                term_overlap_score = term_overlap_count / math.sqrt(max(1, len(query_tokens_text)))
                match_reasons.append(
                    f"term_overlap={term_overlap_count} (query tokens matched candidate text)"
                )

            # Error signature overlap (higher weight).
            signature_basis_tokens = query_error_tokens or query_tokens_text
            error_signature_match_count = _overlap_size(signature_basis_tokens, candidate_error_tokens)
            error_signature_score = 0.0
            if error_signature_match_count > 0:
                error_signature_score = 2.0 * (
                    error_signature_match_count / math.sqrt(max(1, len(signature_basis_tokens)))
                )
                match_reasons.append(
                    f"error_signature_match={error_signature_match_count} (overlap with error signature)"
                )

            # Metadata boosts (optional filters).
            service_score = 0.0
            if candidate_filters["service"]:
                if bug.service == candidate_filters["service"]:
                    service_score = 0.7
                    match_reasons.append("service_match")
            environment_score = 0.0
            if candidate_filters["environment"]:
                if bug.environment == candidate_filters["environment"]:
                    environment_score = 0.4
                    match_reasons.append("environment_match")

            label_overlap = 0
            labels_score = 0.0
            if candidate_filters["labels"]:
                label_overlap = _overlap_size(candidate_filters["labels"], bug.labels)
                if label_overlap > 0:
                    labels_score = 0.25 * label_overlap
                    match_reasons.append(f"label_overlap={label_overlap}")

            # Category match (light boost) when category tokens appear in the query.
            category_tokens = tokenize(bug.category)
            category_overlap = _overlap_size(query_tokens_text, category_tokens)
            category_score = 0.0
            if category_overlap > 0:
                category_score = 0.2 * category_overlap
                match_reasons.append(f"category_match={category_overlap}")

            score = (
                1.0 * term_overlap_score
                + 1.0 * error_signature_score
                + service_score
                + environment_score
                + labels_score
                + category_score
            )

            if score <= 0.0 or not match_reasons:
                continue

            evidence: list[EvidenceItem] = []
            ev = bug.evidence or {}
            for rb_id in ev.get("runbook_ids", []) or []:
                rb = self._datasets.runbooks.get(rb_id)
                if rb:
                    evidence.append(
                        EvidenceItem(snippet_type="runbook", id=rb.id, text=rb.text[:2000])
                    )
            for cfg_id in ev.get("config_ids", []) or []:
                cfg = self._datasets.configs.get(cfg_id)
                if cfg:
                    evidence.append(
                        EvidenceItem(snippet_type="config", id=cfg.id, text=cfg.text[:2000])
                    )
            for log_id in ev.get("log_ids", []) or []:
                lg = self._datasets.logs.get(log_id)
                if lg:
                    evidence.append(
                        EvidenceItem(snippet_type="log", id=lg.id, text=lg.text[:2000])
                    )

            ranked.append((score, bug.id, bug.created_at, match_reasons, evidence))

        # Deterministic ordering: score desc, then created_at desc, then id asc.
        ranked_sorted = sorted(
            ranked,
            key=lambda x: (-x[0], -x[2].timestamp(), x[1]),
        )[:top_k]

        candidates: list[RetrievedIncident] = []
        for score, bug_id, _created_at, reasons, evidence in ranked_sorted:
            candidates.append(
                RetrievedIncident(
                    id=bug_id,
                    score=round(float(score), 4),
                    match_reasons=reasons,
                    evidence=evidence,
                )
            )

        now = datetime.now(timezone.utc)
        return RetrievalResult(
            query=query,
            top_k=top_k,
            created_at=now,
            candidates=candidates,
        )

