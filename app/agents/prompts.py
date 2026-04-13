"""Prompt builders for bug triage analysis."""

from __future__ import annotations

from app.schemas.issue import NormalizedIssue
from app.schemas.retrieval import RetrievalResult


def build_system_prompt() -> str:
    """System prompt with strict guardrails and JSON-only expectation."""
    return (
        "You are a careful bug triage assistant. "
        "Use only provided evidence. "
        "Never claim the issue is fixed. "
        "Always include uncertainty when confidence is low. "
        "Return JSON matching the required schema."
    )


def build_user_prompt(issue: NormalizedIssue, retrieval: RetrievalResult) -> str:
    """Compose user prompt from normalized issue and retrieval evidence."""
    evidence_lines: list[str] = []
    for idx, cand in enumerate(retrieval.candidates[:5], start=1):
        evidence_lines.append(
            f"{idx}. incident={cand.id} score={cand.score} reasons={'; '.join(cand.match_reasons)}"
        )
        for ev in cand.evidence[:2]:
            snippet = ev.text.replace("\n", " ").strip()
            evidence_lines.append(
                f"   - {ev.snippet_type}:{ev.id} text={snippet[:220]}"
            )

    comments = "\n".join(
        [f"- {c.author or 'unknown'}: {c.body[:240]}" for c in issue.comments[:5]]
    )

    return (
        f"Issue ID: {issue.issue_key}\n"
        f"Title: {issue.title}\n"
        f"Description: {issue.description}\n"
        f"Service: {issue.service or 'unknown'}\n"
        f"Environment: {issue.environment or 'unknown'}\n"
        f"Labels: {', '.join(issue.labels) if issue.labels else 'none'}\n"
        f"Comments:\n{comments if comments else '- none'}\n\n"
        f"Retrieved evidence:\n{chr(10).join(evidence_lines) if evidence_lines else '- none'}\n\n"
        "Produce a structured triage JSON output with confidence and no auto-fix claims."
    )

