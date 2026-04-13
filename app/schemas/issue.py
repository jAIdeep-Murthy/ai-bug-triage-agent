"""Internal normalized issue schemas used across service layers."""

from __future__ import annotations

from pydantic import BaseModel, Field


class NormalizedAttachmentMetadata(BaseModel):
    id: str
    filename: str | None = None
    mime_type: str | None = None
    size: int | None = None


class NormalizedComment(BaseModel):
    id: str
    author: str | None = None
    body: str = ""
    created: str | None = None


class NormalizedIssue(BaseModel):
    issue_id: str
    issue_key: str
    title: str
    description: str = ""
    labels: list[str] = Field(default_factory=list)
    status: str | None = None
    priority: str | None = None
    issue_type: str | None = None
    assignee: str | None = None
    reporter: str | None = None
    service: str | None = None
    environment: str | None = None
    comments: list[NormalizedComment] = Field(default_factory=list)
    attachments_metadata: list[NormalizedAttachmentMetadata] = Field(default_factory=list)
    derived_text: str

