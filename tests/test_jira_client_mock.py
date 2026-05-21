from __future__ import annotations

from app.integrations.jira_client import JiraClient

from app.core.config import Settings


def test_jira_client_uses_mock_mode_without_live_env() -> None:
    client = JiraClient(settings=Settings(jira_base_url="", jira_email="", jira_api_token=""))
    assert client.mode == "mock"

    bundle = client.get_issue_bundle("BUG-123")
    assert bundle.source_mode == "mock"
    assert bundle.issue.key == "BUG-123"
    assert bundle.issue.fields.summary
    assert isinstance(bundle.comments, list)
    assert isinstance(bundle.attachments_metadata, list)
