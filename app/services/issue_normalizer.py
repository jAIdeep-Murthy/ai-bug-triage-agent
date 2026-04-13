"""Normalize Jira issue payloads into internal typed issue schema."""

from __future__ import annotations

from typing import Any

from app.schemas.issue import (
    NormalizedAttachmentMetadata,
    NormalizedComment,
    NormalizedIssue,
)
from app.schemas.jira import JiraIssueBundle


def _flatten_rich_text(value: Any) -> str:
    """Flatten string/dict/list rich text bodies to plain text."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        parts: list[str] = []
        if "text" in value and isinstance(value["text"], str):
            parts.append(value["text"])
        for maybe_child_key in ("content", "attrs"):
            child = value.get(maybe_child_key)
            if child is not None:
                parts.append(_flatten_rich_text(child))
        return " ".join([p for p in parts if p]).strip()
    if isinstance(value, list):
        return " ".join([_flatten_rich_text(x) for x in value if x is not None]).strip()
    return str(value).strip()


def _derive_service(labels: list[str], title: str, description: str) -> str | None:
    for label in labels:
        if label.startswith("service:"):
            return label.split(":", 1)[1]
    text = f"{title} {description}".lower()
    for candidate in ["auth", "payments", "notifications", "search", "frontend", "billing"]:
        if candidate in text:
            return candidate
    return None


def _derive_environment(labels: list[str], title: str, description: str) -> str | None:
    for label in labels:
        if label.startswith("env:"):
            return label.split(":", 1)[1]
    text = f"{title} {description}".lower()
    for candidate in ["prod", "production", "staging", "dev"]:
        if candidate in text:
            if candidate == "production":
                return "prod"
            return candidate
    return None


def normalize_jira_issue(bundle: JiraIssueBundle) -> NormalizedIssue:
    """Map Jira issue bundle to internal normalized issue schema."""
    issue = bundle.issue
    fields = issue.fields

    description = _flatten_rich_text(fields.description)
    comments = [
        NormalizedComment(
            id=c.id,
            author=(c.author.displayName if c.author else None),
            body=_flatten_rich_text(c.body),
            created=c.created,
        )
        for c in bundle.comments
    ]

    attachments = [
        NormalizedAttachmentMetadata(
            id=a.id,
            filename=a.filename,
            mime_type=a.mimeType,
            size=a.size,
        )
        for a in bundle.attachments_metadata
    ]

    title = fields.summary or ""
    labels = fields.labels or []
    service = _derive_service(labels, title, description)
    environment = _derive_environment(labels, title, description)

    derived_text_parts = [title, description] + [c.body for c in comments if c.body]
    derived_text = "\n".join([x for x in derived_text_parts if x]).strip()

    return NormalizedIssue(
        issue_id=issue.id,
        issue_key=issue.key,
        title=title,
        description=description,
        labels=labels,
        status=(fields.status.name if fields.status else None),
        priority=(fields.priority.name if fields.priority else None),
        issue_type=(fields.issuetype.name if fields.issuetype else None),
        assignee=(fields.assignee.displayName if fields.assignee else None),
        reporter=(fields.reporter.displayName if fields.reporter else None),
        service=service,
        environment=environment,
        comments=comments,
        attachments_metadata=attachments,
        derived_text=derived_text,
    )

