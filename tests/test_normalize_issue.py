from __future__ import annotations

import json
from pathlib import Path

from app.integrations.jira_client import extract_issue_key_from_webhook
from app.schemas.jira import JiraComment, JiraIssue, JiraIssueBundle
from app.services.issue_normalizer import normalize_jira_issue


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent / "fixtures" / name


def _load_json_fixture(name: str) -> dict:
    # Fixtures may include UTF-8 BOM when written by PowerShell.
    return json.loads(_fixture_path(name).read_text(encoding="utf-8-sig"))


def test_normalize_jira_issue_from_fixture() -> None:
    issue_payload = _load_json_fixture("jira_issue_rest_sample.json")
    issue = JiraIssue.model_validate(issue_payload)

    comments = [
        JiraComment.model_validate(
            {
                "id": "c-99",
                "body": "Staging failures started right after secret rotation.",
                "author": {"displayName": "Payments Ops"},
                "created": "2026-04-08T08:10:00.000+0000",
            }
        )
    ]

    bundle = JiraIssueBundle(
        issue=issue,
        comments=comments,
        attachments_metadata=issue.fields.attachment,
        source_mode="mock",
    )

    normalized = normalize_jira_issue(bundle)
    assert normalized.issue_id == "10099"
    assert normalized.issue_key == "BUG-99"
    assert normalized.title.startswith("Payments webhook")
    assert normalized.service == "payments"
    assert normalized.environment == "staging"
    assert len(normalized.comments) == 1
    assert "secret rotation" in normalized.derived_text


def test_extract_issue_key_from_webhook_fixture() -> None:
    payload = _load_json_fixture("jira_webhook_sample.json")
    key = extract_issue_key_from_webhook(payload)
    assert key == "BUG-99"
