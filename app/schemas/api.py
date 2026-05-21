"""API request/response schemas for Unit 5 routes."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Union

from pydantic import BaseModel, Field, model_validator

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
    issue_id: str | None = Field(default=None, max_length=128)
    issue_key: str | None = Field(default=None, max_length=128)
    rating: Union[int, Literal["helpful", "partially_helpful", "not_helpful"]]
    comment: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="before")
    @classmethod
    def preprocess_payload(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        
        # 1. Alias issue_key -> issue_id
        if "issue_key" in data and not data.get("issue_id"):
            data["issue_id"] = data["issue_key"]
        if "issue_id" in data and not data.get("issue_key"):
            data["issue_key"] = data["issue_id"]

        # 2. Map integer rating
        rating = data.get("rating")
        if isinstance(rating, int):
            if rating in (4, 5):
                data["rating"] = "helpful"
            elif rating == 3:
                data["rating"] = "partially_helpful"
            elif rating in (1, 2):
                data["rating"] = "not_helpful"
        elif isinstance(rating, str):
            if rating.isdigit():
                val = int(rating)
                if val in (4, 5):
                    data["rating"] = "helpful"
                elif val == 3:
                    data["rating"] = "partially_helpful"
                elif val in (1, 2):
                    data["rating"] = "not_helpful"

        return data

    @model_validator(mode="after")
    def validate_presence(self) -> "FeedbackRequest":
        if (not self.issue_id or not self.issue_id.strip()) and (not self.issue_key or not self.issue_key.strip()):
            raise ValueError("Either issue_id or issue_key must be provided")
        return self


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


class DuplicateCandidate(BaseModel):
    issue_key: str
    similarity_score: float


class DuplicateCheckResult(BaseModel):
    issue_key: str
    is_likely_duplicate: bool
    primary_duplicate_key: str | None
    candidates: list[DuplicateCandidate]


class CommentPostResponse(BaseModel):
    issue_id: str
    comment_posted: bool
    mode: Literal["live", "mock"]
    comment_id: str | None = None


