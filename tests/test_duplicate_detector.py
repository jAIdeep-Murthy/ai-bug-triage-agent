"""Tests for the duplicate detection feature."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.issue import NormalizedIssue
from app.services.duplicate_detector import check_duplicate

@pytest.fixture
def dummy_normalized() -> NormalizedIssue:
    return NormalizedIssue(
        issue_id="9999",
        issue_key="BUG-9999",
        title="Test issue",
        description="Test description",
        labels=[],
        status="Open",
        priority="High",
        issue_type="Bug",
        assignee=None,
        reporter=None,
        service="auth",
        environment="prod",
        comments=[],
        attachments_metadata=[],
        derived_text="Test issue Test description",
    )

@patch("app.services.duplicate_detector.get_vector_store")
def test_likely_duplicate(mock_get_vs, dummy_normalized):
    mock_vs = MagicMock()
    mock_get_vs.return_value = mock_vs
    mock_vs.count.return_value = 10
    mock_vs.semantic_search.return_value = [
        {"issue_key": "JDT-1234", "similarity_score": 0.95}
    ]
    
    result = check_duplicate(dummy_normalized, threshold=0.9)
    assert result.is_likely_duplicate is True
    assert result.primary_duplicate_key == "JDT-1234"
    assert len(result.candidates) == 1

@patch("app.services.duplicate_detector.get_vector_store")
def test_not_duplicate(mock_get_vs, dummy_normalized):
    mock_vs = MagicMock()
    mock_get_vs.return_value = mock_vs
    mock_vs.count.return_value = 10
    mock_vs.semantic_search.return_value = [
        {"issue_key": "JDT-1234", "similarity_score": 0.75}
    ]
    
    result = check_duplicate(dummy_normalized, threshold=0.9)
    assert result.is_likely_duplicate is False
    assert result.primary_duplicate_key is None
    assert len(result.candidates) == 0

@patch("app.services.duplicate_detector.get_vector_store")
def test_self_match_excluded(mock_get_vs, dummy_normalized):
    mock_vs = MagicMock()
    mock_get_vs.return_value = mock_vs
    mock_vs.count.return_value = 10
    mock_vs.semantic_search.return_value = [
        {"issue_key": "BUG-9999", "similarity_score": 0.99}
    ]
    
    result = check_duplicate(dummy_normalized, threshold=0.9)
    assert result.is_likely_duplicate is False
    assert len(result.candidates) == 0

@patch("app.services.duplicate_detector.get_vector_store")
def test_vector_store_failure(mock_get_vs, dummy_normalized):
    mock_get_vs.side_effect = Exception("Chroma DB offline")
    
    result = check_duplicate(dummy_normalized, threshold=0.9)
    assert result.is_likely_duplicate is False
    assert len(result.candidates) == 0

@patch("app.services.duplicate_detector.get_vector_store")
def test_empty_results(mock_get_vs, dummy_normalized):
    mock_vs = MagicMock()
    mock_get_vs.return_value = mock_vs
    mock_vs.count.return_value = 10
    mock_vs.semantic_search.return_value = []
    
    result = check_duplicate(dummy_normalized, threshold=0.9)
    assert result.is_likely_duplicate is False
    assert len(result.candidates) == 0

client = TestClient(app)

@patch("app.api.issues.check_duplicate")
@patch("app.api.issues.normalize_jira_issue")
@patch("app.integrations.jira_client.JiraClient.get_issue_bundle")
def test_duplicates_endpoint_likely(mock_get_bundle, mock_normalize, mock_check):
    mock_get_bundle.return_value = MagicMock()
    mock_normalize.return_value = MagicMock()
    
    from app.schemas.api import DuplicateCheckResult, DuplicateCandidate
    
    mock_check.return_value = DuplicateCheckResult(
        issue_key="BUG-10001",
        is_likely_duplicate=True,
        primary_duplicate_key="JDT-555",
        candidates=[DuplicateCandidate(issue_key="JDT-555", similarity_score=0.96)]
    )
    
    resp = client.get("/issues/BUG-10001/duplicates")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_likely_duplicate"] is True
    assert data["primary_duplicate_key"] == "JDT-555"

@patch("app.api.issues.check_duplicate")
@patch("app.api.issues.normalize_jira_issue")
@patch("app.integrations.jira_client.JiraClient.get_issue_bundle")
def test_duplicates_endpoint_no_match(mock_get_bundle, mock_normalize, mock_check):
    mock_get_bundle.return_value = MagicMock()
    mock_normalize.return_value = MagicMock()
    
    from app.schemas.api import DuplicateCheckResult
    
    mock_check.return_value = DuplicateCheckResult(
        issue_key="BUG-10001",
        is_likely_duplicate=False,
        primary_duplicate_key=None,
        candidates=[]
    )
    
    resp = client.get("/issues/BUG-10001/duplicates")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_likely_duplicate"] is False
    assert data["primary_duplicate_key"] is None
