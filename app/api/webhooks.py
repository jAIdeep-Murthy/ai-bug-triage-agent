"""Webhook endpoint wiring for Jira events (Unit 5)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_triage_pipeline
from app.integrations.jira_client import extract_issue_key_from_webhook
from app.schemas.api import WebhookRequest, WebhookResponse
from app.services.triage_pipeline import AnalysisExecutionError, IssueFetchError, TriagePipeline

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/jira", response_model=WebhookResponse)
def handle_jira_webhook(
    request: WebhookRequest,
    pipeline: TriagePipeline = Depends(get_triage_pipeline),
) -> WebhookResponse:
    issue_key = extract_issue_key_from_webhook(request.payload)
    if not issue_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook payload missing issue.key.",
        )

    try:
        pipeline.analyze_issue(issue_key)
    except IssueFetchError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except AnalysisExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(exc)) from exc

    return WebhookResponse(accepted=True, issue_key=issue_key, analysis_recorded=True)

