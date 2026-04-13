"""Custom analysis orchestration (LangGraph-ready interface, not LangGraph-first)."""

from __future__ import annotations

from pydantic import ValidationError

from app.agents.model_client import ModelClient, OllamaModelClient
from app.agents.prompts import build_system_prompt, build_user_prompt
from app.schemas.analysis import AnalysisDiagnostics, AnalysisResult, AnalysisRunResult
from app.schemas.issue import NormalizedIssue
from app.schemas.retrieval import RetrievalResult
from app.core.config import get_settings
from app.services.json_repair import repair_json_text


class AnalysisOrchestrator:
    """Coordinates prompt creation, model call, JSON validation, and repair fallback."""

    def __init__(self, model_client: ModelClient | None = None):
        self.settings = get_settings()
        self.demo_mode_enabled = bool(self.settings.demo_mode) and model_client is None
        self.model_client = model_client or OllamaModelClient()

    def run(self, issue: NormalizedIssue, retrieval: RetrievalResult) -> AnalysisRunResult:
        if self.demo_mode_enabled:
            analysis = AnalysisResult(
                issue_id=issue.issue_key,
                summary=(
                    "Demo mode: likely transient dependency/service outage causing downstream failures."
                ),
                category="dependency",
                severity="medium",
                likely_owner_team="platform-runtime",
                confidence=0.72,
                possible_root_causes=[
                    "Upstream dependency returning 5xx or timing out",
                    "Recent version bump or config change introduced incompatibility",
                ],
                evidence=[
                    "Synthetic historical incidents show similar error signatures when upstream APIs degrade.",
                    "Issue metadata indicates service/env scope consistent with dependency failures.",
                ],
                similar_issues=["INC-1042", "BUG-778", "BUG-551"],
                recommended_steps=[
                    "Confirm whether the upstream dependency is degraded (status page / metrics / logs).",
                    "Check recent deploys/config changes for the affected service and upstream dependency.",
                    "Collect a minimal failing request trace (request id) and correlate across services.",
                    "If timeouts are present, verify retry/backoff settings and circuit breaker thresholds.",
                ],
                missing_information=[
                    "Representative stack trace or error snippet from logs",
                    "Time window of first occurrence and whether it correlates with a deploy",
                ],
                jira_comment_draft=(
                    "Demo mode result (no Ollama call). Suggested next checks:\n"
                    "1) Verify upstream dependency health (5xx/latency) in the incident window.\n"
                    "2) Review recent deploy/config changes affecting this service and upstream.\n"
                    "3) Share a request id / stack trace to tighten root cause.\n"
                    "Human review required before any remediation."
                ),
            )
            diagnostics = AnalysisDiagnostics(
                model_name="demo_mode",
                raw_response_length=0,
                used_repair=False,
                validation_error=None,
            )
            return AnalysisRunResult(analysis=analysis, diagnostics=diagnostics)

        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(issue, retrieval)
        schema = AnalysisResult.model_json_schema()

        response = self.model_client.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_schema=schema,
        )

        diagnostics = AnalysisDiagnostics(
            model_name=response.model_name,
            raw_response_length=len(response.content),
            used_repair=False,
            validation_error=None,
        )

        try:
            analysis = AnalysisResult.model_validate_json(response.content)
        except ValidationError as exc:
            repaired = repair_json_text(response.content)
            diagnostics.used_repair = repaired.used_repair
            diagnostics.validation_error = str(exc)
            analysis = AnalysisResult.model_validate_json(repaired.text)

        # Ensure issue id consistency with normalized issue key.
        if not analysis.issue_id:
            analysis.issue_id = issue.issue_key
        return AnalysisRunResult(analysis=analysis, diagnostics=diagnostics)

