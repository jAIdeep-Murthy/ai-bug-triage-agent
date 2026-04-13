"""Analysis output schemas for AI triage orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, model_validator


AnalysisCategory = Literal[
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

SeverityLevel = Literal["low", "medium", "high"]


class AnalysisResult(BaseModel):
    issue_id: str
    summary: str
    category: AnalysisCategory
    severity: SeverityLevel
    likely_owner_team: str
    confidence: float = Field(ge=0.0, le=1.0)
    possible_root_causes: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    similar_issues: list[str] = Field(default_factory=list)
    recommended_steps: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    jira_comment_draft: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    needs_human_review: bool = False
    uncertainty_note: str | None = None

    @model_validator(mode="after")
    def apply_guardrails(self) -> "AnalysisResult":
        """Enforce human-in-the-loop guardrails based on confidence and wording."""
        if self.confidence < 0.65:
            self.needs_human_review = True
            if not self.uncertainty_note:
                self.uncertainty_note = (
                    "Low-confidence triage. Human review required before any action."
                )

        lower_comment = self.jira_comment_draft.lower()
        forbidden_phrases = [
            "issue fixed",
            "bug fixed",
            "resolved automatically",
            "auto-closed",
        ]
        for phrase in forbidden_phrases:
            if phrase in lower_comment:
                raise ValueError(
                    "jira_comment_draft violates guardrail wording (claims issue fixed/auto action)."
                )
        return self


class AnalysisDiagnostics(BaseModel):
    model_name: str
    used_repair: bool = False
    raw_response_length: int = 0
    validation_error: str | None = None


class AnalysisRunResult(BaseModel):
    analysis: AnalysisResult
    diagnostics: AnalysisDiagnostics

