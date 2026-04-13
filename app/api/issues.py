"""Issue analysis and report endpoints."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.api.deps import get_analysis_store, get_triage_pipeline
from app.schemas.analysis import AnalysisResult
from app.schemas.api import AnalyzeResponse, ReportResponse
from app.services.analysis_store import AnalysisStore
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

