"""Unit 5 triage pipeline: Jira -> normalize -> retrieve -> analyze -> persist."""

from __future__ import annotations

import json

import httpx
from pydantic import ValidationError

from app.agents.orchestrator import AnalysisOrchestrator
from app.agents.model_client import OllamaConnectionError
from app.core.config import get_settings
from app.integrations.jira_client import JiraClient
from app.retrieval.keyword_retrieval import KeywordRetrievalEngine
from app.schemas.analysis import AnalysisRunResult
from app.schemas.retrieval import EvidenceItem, RetrievalQuery, RetrievedIncident
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

        # Semantic vector retrieval (Upgrade 3)
        settings = get_settings()
        if settings.vector_search_enabled:
            try:
                from app.services.vector_store import get_vector_store

                vector_store = get_vector_store(settings=settings)
                if vector_store.count() > 0:
                    query_text = f"{normalized.title} {normalized.description}"[:512]
                    semantic_hits = vector_store.semantic_search(
                        query_text=query_text,
                        n_results=5,
                    )
                    id_to_candidate = {c.id: c for c in retrieval.candidates}
                    existing_keys = set(id_to_candidate.keys())
                    semantic_candidates: list[RetrievedIncident] = []
                    for hit in semantic_hits:
                        hit_key = str(hit.get("issue_key") or "")
                        if not hit_key or hit_key in existing_keys:
                            # Even if the hit overlaps with a keyword candidate, ensure
                            # semantic context is visible to the LLM by augmenting
                            # match_reasons for that candidate.
                            if hit_key and hit_key in id_to_candidate:
                                semantic_reason = (
                                    "semantic similarity "
                                    + f"{float(hit.get('similarity_score') or 0.0):.2f}"
                                )
                                cand = id_to_candidate[hit_key]
                                if not any(
                                    isinstance(r, str)
                                    and "semantic similarity" in r
                                    for r in cand.match_reasons
                                ):
                                    cand.match_reasons.append(semantic_reason)
                            continue

                        semantic_reason = (
                            "semantic similarity "
                            + f"{float(hit.get('similarity_score') or 0.0):.2f}"
                        )
                        semantic_candidates.append(
                            RetrievedIncident(
                                id=hit_key,
                                score=float(hit.get("similarity_score") or 0.0),
                                match_reasons=[semantic_reason],
                                # Give semantic candidates at least one evidence snippet
                                # so the LLM is more likely to echo them in the output.
                                evidence=[
                                    EvidenceItem(
                                        snippet_type="log",
                                        id=hit_key,
                                        text=str(hit.get("text") or "")[:2000],
                                    )
                                ],
                            )
                        )
                        existing_keys.add(hit_key)

                    # Prepend semantic hits so they are included in retrieval.candidates[:5]
                    # (the prompt only uses the first five candidates).
                    if semantic_candidates:
                        retrieval.candidates = semantic_candidates + retrieval.candidates
            except Exception as exc:
                import logging

                logging.getLogger(__name__).warning(
                    "Vector search failed, falling back to keyword only: %s",
                    exc,
                )

        # Apply feedback-driven scoring adjustment (Upgrade 6)
        try:
            from app.services.feedback_store import FeedbackStore
            from app.services.retrieval_scorer import apply_feedback_scores

            f_store = FeedbackStore(self.analysis_store.db)
            cand_keys = [c.id for c in retrieval.candidates]
            multipliers = f_store.get_multipliers_for_keys(cand_keys)
            
            adjusted = apply_feedback_scores(retrieval.candidates, multipliers)
            retrieval.candidates = adjusted
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(
                "Feedback scoring adjustment failed, falling back to unweighted: %s",
                exc,
            )

        try:
            run_result = self.orchestrator.run(normalized, retrieval)
        except (ValidationError, json.JSONDecodeError, ValueError) as exc:
            raise AnalysisExecutionError(f"Model output could not be validated: {exc}") from exc
        except OllamaConnectionError as exc:
            raise AnalysisExecutionError(str(exc)) from exc
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

