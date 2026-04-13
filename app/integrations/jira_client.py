"""Jira integration with env-driven live mode and mock fallback."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.schemas.jira import (
    JiraAttachmentMetadata,
    JiraComment,
    JiraIssue,
    JiraIssueBundle,
)


def extract_issue_key_from_webhook(payload: dict[str, Any]) -> str | None:
    """Extract Jira issue key from webhook payload when present."""
    issue = payload.get("issue")
    if not isinstance(issue, dict):
        return None
    key = issue.get("key")
    if isinstance(key, str) and key.strip():
        return key
    return None


class JiraClient:
    """Jira client that supports live API mode and deterministic mock fallback."""

    def __init__(self, settings: Settings | None = None, timeout_seconds: float = 10.0):
        self.settings = settings or get_settings()
        self._timeout = timeout_seconds

    @property
    def mode(self) -> str:
        return self.settings.jira_mode

    def get_issue_bundle(self, issue_id: str) -> JiraIssueBundle:
        """Fetch issue + comments + attachment metadata via live or mock mode."""
        if self.mode == "live":
            return self._get_issue_bundle_live(issue_id)
        return self._get_issue_bundle_mock(issue_id)

    def _get_issue_bundle_live(self, issue_id: str) -> JiraIssueBundle:
        """Fetch data from Jira Cloud REST endpoints."""
        base_url = (self.settings.jira_base_url or "").rstrip("/")
        user = self.settings.jira_email or self.settings.jira_user
        token = self.settings.jira_api_token or ""
        if not base_url or not user or not token:
            # Fail closed to mock mode behavior when credentials are incomplete.
            return self._get_issue_bundle_mock(issue_id)

        auth = (user, token)
        headers = {"Accept": "application/json"}

        issue_url = f"{base_url}/rest/api/3/issue/{issue_id}"
        comments_url = f"{base_url}/rest/api/3/issue/{issue_id}/comment"

        with httpx.Client(timeout=self._timeout) as client:
            issue_response = client.get(issue_url, headers=headers, auth=auth)
            issue_response.raise_for_status()
            issue_raw = issue_response.json()

            comments_response = client.get(comments_url, headers=headers, auth=auth)
            comments_response.raise_for_status()
            comments_raw = comments_response.json()

        issue = JiraIssue.model_validate(issue_raw)
        comments = [
            JiraComment.model_validate(x) for x in (comments_raw.get("comments", []) or [])
        ]
        attachments = issue.fields.attachment

        return JiraIssueBundle(
            issue=issue,
            comments=comments,
            attachments_metadata=attachments,
            source_mode="live",
        )

    def _get_issue_bundle_mock(self, issue_id: str) -> JiraIssueBundle:
        """Return deterministic mock issue data for local dev and tests."""
        issue = JiraIssue.model_validate(
            {
                "id": "10001",
                "key": issue_id,
                "fields": {
                    "summary": "Auth requests intermittently timing out in production",
                    "description": (
                        "Engineers report spikes in auth failures after deploy.\n"
                        "Error signature includes upstream timeout while validating token claims."
                    ),
                    "labels": ["service:auth", "env:prod", "bug", "priority:high"],
                    "status": {"name": "To Do"},
                    "priority": {"name": "High"},
                    "issuetype": {"name": "Bug"},
                    "assignee": {"displayName": "Unassigned"},
                    "reporter": {"displayName": "API Gateway Monitor"},
                    "attachment": [
                        {
                            "id": "att-001",
                            "filename": "auth-timeout.log",
                            "mimeType": "text/plain",
                            "size": 5420,
                        }
                    ],
                },
            }
        )

        comments = [
            JiraComment.model_validate(
                {
                    "id": "c-1",
                    "body": "Observed from 14:10 UTC to 14:18 UTC. Affected login endpoint only.",
                    "author": {"displayName": "OnCall Engineer"},
                    "created": "2026-04-01T14:20:00.000+0000",
                }
            ),
            JiraComment.model_validate(
                {
                    "id": "c-2",
                    "body": "Potentially related to token introspection latency from upstream provider.",
                    "author": {"displayName": "Identity Team"},
                    "created": "2026-04-01T14:24:00.000+0000",
                }
            ),
        ]

        return JiraIssueBundle(
            issue=issue,
            comments=comments,
            attachments_metadata=issue.fields.attachment or [],
            source_mode="mock",
        )

