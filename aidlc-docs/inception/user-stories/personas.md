# User Personas

## P1 — Alex (Backend / On-Call Engineer)
- **Goal**: Understand what is likely wrong, who should own the issue, and what to verify next.
- **Context**: Receives Jira bugs and incidents; needs structured output, not a generic chat.
- **Pain**: Scattered context, duplicate incidents, unclear ownership.
- **Success**: Actionable triage artifact with confidence, evidence references, and explicit gaps.

## P2 — Jordan (Platform / Service Owner)
- **Goal**: Run the triage service locally with predictable config; integrate Jira webhooks safely.
- **Context**: Owns deployment and secrets via env vars; cares about observability and guardrails.
- **Pain**: Opaque failures, accidental automation, secret leakage in logs.
- **Success**: Health checks, structured logs, read-only Jira posture, no production side effects.

## P3 — Sam (Reviewer / Hiring Manager Perspective)
- **Goal**: Assess architecture clarity, testing, and responsible AI use.
- **Context**: Reads README and repo structure.
- **Pain**: “Demoware” without tests or boundaries.
- **Success**: Clear layers, documented constraints, pytest coverage on core paths.
