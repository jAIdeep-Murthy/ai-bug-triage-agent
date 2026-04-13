"""Unit 5 triage pipeline: Jira -> normalize -> retrieve -> analyze -> persist."""

from __future__ import annotations

import json

import httpx
from pydantic import ValidationError

from app.agents.orchestrator import AnalysisOrchestrator
from app.integrations.jira_client import JiraClient
from app.retrieval.keyword_retrieval import KeywordRetrievalEngine
from app.schemas.analysis import AnalysisRunResult
from app.schemas.retrieval import RetrievalQuery
from app.services.analysis_store import AnalysisStore
from app.services.dataset_loader import SyntheticDatasets
from app.services.issue_normalizer import normalize_jira_issue


class TriagePipelineError(Exception):
    """Base pipeline exception for API mapping."""


class IssueFetchError(TriagePipelineError):
    pass


class AnalysisExecutionError(TriagePipelineError):
    pass


class TriagePipeline:
    def __init__(
        self,
        *,
        jira_client: JiraClient,
        retrieval_engine: KeywordRetrievalEngine,
        orchestrator: AnalysisOrchestrator,
        analysis_store: AnalysisStore,
    ):
        self.jira_client = jira_client
        self.retrieval_engine = retrieval_engine
        self.orchestrator = orchestrator
        self.analysis_store = analysis_store

    @classmethod
    def from_defaults(
        cls, *, datasets: SyntheticDatasets, analysis_store: AnalysisStore
    ) -> "TriagePipeline":
        return cls(
            jira_client=JiraClient(),
            retrieval_engine=KeywordRetrievalEngine(datasets),
            orchestrator=AnalysisOrchestrator(),
            analysis_store=analysis_store,
        )

    def analyze_issue(self, issue_id: str) -> tuple[AnalysisRunResult, int, str]:
        """Run full triage flow and persist the resulting analysis."""
        try:
            bundle = self.jira_client.get_issue_bundle(issue_id)
        except httpx.TimeoutException as exc:
            raise IssueFetchError("Timed out while fetching issue from Jira.") from exc
        except httpx.HTTPError as exc:
            raise IssueFetchError("Failed Jira request for issue fetch.") from exc
        except ValidationError as exc:
            raise IssueFetchError("Received invalid Jira payload shape.") from exc

        normalized = normalize_jira_issue(bundle)
        retrieval_query = RetrievalQuery(
            text_query=normalized.derived_text or normalized.title,
            service=normalized.service,
            environment=normalized.environment,
            labels=normalized.labels,
        )
        retrieval = self.retrieval_engine.retrieve(retrieval_query, top_k=5)

        try:
            run_result = self.orchestrator.run(normalized, retrieval)
        except (ValidationError, json.JSONDecodeError, ValueError) as exc:
            raise AnalysisExecutionError("Model output could not be validated.") from exc
        except httpx.TimeoutException as exc:
            raise AnalysisExecutionError("Timed out while waiting for model response.") from exc
        except httpx.HTTPError as exc:
            raise AnalysisExecutionError("Model service request failed.") from exc

        record_id = self.analysis_store.save_analysis(
            issue_id=normalized.issue_id,
            issue_key=normalized.issue_key,
            analysis=run_result.analysis,
        )
        return run_result, record_id, bundle.source_mode

