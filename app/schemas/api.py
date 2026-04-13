"""API request/response schemas for Unit 5 routes."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.analysis import AnalysisDiagnostics, AnalysisResult


class AnalyzeResponse(BaseModel):
    issue_id: str
    source_mode: str
    analysis: AnalysisResult
    diagnostics: AnalysisDiagnostics


class ReportResponse(BaseModel):
    issue_id: str
    analysis: AnalysisResult


class FeedbackRequest(BaseModel):
    issue_id: str = Field(min_length=1, max_length=128)
    rating: Literal["helpful", "partially_helpful", "not_helpful"]
    comment: str | None = Field(default=None, max_length=5000)


class FeedbackResponse(BaseModel):
    feedback_id: int
    issue_id: str
    created_at: datetime


class WebhookRequest(BaseModel):
    payload: dict[str, Any]


class WebhookResponse(BaseModel):
    accepted: bool
    issue_key: str
    analysis_recorded: bool

