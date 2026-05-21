"""Issue analysis and report endpoints."""

from __future__ import annotations

import json
import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.api.deps import get_analysis_store, get_triage_pipeline
from app.schemas.analysis import AnalysisResult
from app.schemas.api import AnalyzeResponse, ReportResponse, DuplicateCheckResult, CommentPostResponse
from app.services.analysis_store import AnalysisStore
from app.services.duplicate_detector import check_duplicate
from app.services.issue_normalizer import normalize_jira_issue
from app.services.triage_pipeline import (
    AnalysisExecutionError,
    IssueFetchError,
    TriagePipeline,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/issues", tags=["issues"])


@router.get("/{issue_id}/analyze", response_model=AnalyzeResponse)
def analyze_issue(
    issue_id: str = Path(min_length=1, max_length=128),
    pipeline: TriagePipeline = Depends(get_triage_pipeline),
) -> AnalyzeResponse:
    try:
        result, _record_id, source_mode = pipeline.analyze_issue(issue_id)
    except IssueFetchError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except AnalysisExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected analyze failure for issue_id=%s", issue_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected analysis error.") from exc

    return AnalyzeResponse(
        issue_id=issue_id,
        source_mode=source_mode,
        analysis=result.analysis,
        diagnostics=result.diagnostics,
    )


@router.get("/{issue_id}/report", response_model=ReportResponse)
def get_report(
    issue_id: str = Path(min_length=1, max_length=128),
    store: AnalysisStore = Depends(get_analysis_store),
) -> ReportResponse:
    record = store.get_latest_by_issue(issue_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analysis report found for issue_id={issue_id}.",
        )
    analysis = AnalysisResult.model_validate(json.loads(record.analysis_json))
    return ReportResponse(issue_id=issue_id, analysis=analysis)


@router.get("/{issue_id}/duplicates", response_model=DuplicateCheckResult)
def get_duplicates(
    issue_id: str = Path(min_length=1, max_length=128),
    pipeline: TriagePipeline = Depends(get_triage_pipeline),
) -> DuplicateCheckResult:
    import httpx
    try:
        bundle = pipeline.jira_client.get_issue_bundle(issue_id)
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Timed out while fetching issue from Jira.") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed Jira request for issue fetch.") from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected failure for issue_id=%s during duplicate check", issue_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error during duplicate check.") from exc

    normalized = normalize_jira_issue(bundle)
    return check_duplicate(normalized)


@router.post("/{issue_id}/comment", response_model=CommentPostResponse)
def post_comment(
    issue_id: str = Path(min_length=1, max_length=128),
    store: AnalysisStore = Depends(get_analysis_store),
    pipeline: TriagePipeline = Depends(get_triage_pipeline),
) -> CommentPostResponse:
    """Post the AI generated comment draft back to the Jira ticket.

    NOTE: Repeated calls to this endpoint may repost the same jira_comment_draft.
    """
    record = store.get_latest_by_issue(issue_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No analysis exists for issue {issue_id}. Run analysis first.",
        )

    try:
        analysis_data = json.loads(record.analysis_json)
        draft = analysis_data.get("jira_comment_draft")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to parse persisted analysis JSON.",
        ) from exc

    if not draft or not draft.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Jira comment draft is missing, empty, or whitespace-only in the persisted analysis.",
        )

    try:
        comment_id = pipeline.jira_client.add_comment(issue_id, draft)
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if status_code in (401, 403):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Jira authentication or authorization error: HTTP {status_code}.",
            ) from exc
        elif status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Jira issue not found: HTTP 404.",
            ) from exc
        else:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Jira client HTTP error: HTTP {status_code}.",
            ) from exc
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Jira service timeout or connection error.",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Jira client network/request error: {str(exc)}",
        ) from exc

    client_mode = pipeline.jira_client.mode
    mode = "live" if (client_mode == "live" and not issue_id.startswith("BUG-")) else "mock"

    return CommentPostResponse(
        issue_id=issue_id,
        comment_posted=True,
        mode=mode,
        comment_id=comment_id,
    )


