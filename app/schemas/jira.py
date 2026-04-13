"""Raw Jira-facing schemas (REST payloads and webhook envelope)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class JiraUserRef(BaseModel):
    accountId: str | None = None
    displayName: str | None = None
    emailAddress: str | None = None


class JiraNamedRef(BaseModel):
    name: str | None = None
    value: str | None = None


class JiraStatusRef(BaseModel):
    name: str | None = None


class JiraAttachmentMetadata(BaseModel):
    id: str
    filename: str | None = None
    mimeType: str | None = None
    size: int | None = None
    content: str | None = None


class JiraIssueFields(BaseModel):
    summary: str = ""
    description: str | dict[str, Any] | None = None
    labels: list[str] = Field(default_factory=list)
    status: JiraStatusRef | None = None
    assignee: JiraUserRef | None = None
    reporter: JiraUserRef | None = None
    priority: JiraNamedRef | None = None
    issuetype: JiraNamedRef | None = None
    attachment: list[JiraAttachmentMetadata] = Field(default_factory=list)
    comment: dict[str, Any] | None = None


class JiraIssue(BaseModel):
    id: str
    key: str
    fields: JiraIssueFields


class JiraComment(BaseModel):
    id: str
    body: str | dict[str, Any] | None = None
    author: JiraUserRef | None = None
    created: str | None = None


class JiraIssueBundle(BaseModel):
    issue: JiraIssue
    comments: list[JiraComment] = Field(default_factory=list)
    attachments_metadata: list[JiraAttachmentMetadata] = Field(default_factory=list)
    source_mode: str


class JiraWebhookPayload(BaseModel):
    issue: dict[str, Any] | None = None
    webhookEvent: str | None = None

