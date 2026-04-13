"""Schemas for retrieval queries and keyword retrieval results."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class RetrievalQuery(BaseModel):
    """A keyword + metadata retrieval query (no embeddings)."""

    text_query: str = Field(min_length=1, max_length=2000)
    service: str | None = Field(default=None, max_length=100)
    environment: str | None = Field(default=None, max_length=50)
    labels: list[str] | None = None

    # Reserved for later unit that can extract signature tokens from text.
    error_signature_tokens: list[str] | None = None


class EvidenceItem(BaseModel):
    snippet_type: Literal["runbook", "config", "log"]
    id: str
    text: str


class RetrievedIncident(BaseModel):
    id: str
    score: float
    match_reasons: list[str]
    evidence: list[EvidenceItem]


class RetrievalResult(BaseModel):
    query: RetrievalQuery
    top_k: int
    created_at: datetime
    candidates: list[RetrievedIncident]

