# Requirements Clarification Questions

Please answer each question by placing the letter in the `[Answer]:` field.

## Question 1
What is your preferred implementation depth for this first delivery?

A) Full MVP in one pass (all requested layers, tests, dashboard, docs)
B) Core backend first (API + retrieval + analysis), then dashboard/tests in next pass
C) Architecture + skeleton + synthetic data + stubs first, then full integration
X) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question 2
How do you want Jira integration handled during local development?

A) Real Jira Cloud integration using env vars + fallback mocks if unset
B) Mock-only mode for now, real Jira client scaffolded but disabled
C) Real Jira only (fail if credentials are missing)
X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 3
How should the AI orchestration be implemented for MVP?

A) Simple custom orchestration service in Python (recommended for clarity)
B) LangGraph flow with explicit nodes/edges
C) Both (custom now, LangGraph-ready abstraction)
X) Other (please describe after [Answer]: tag below)

[Answer]: C

## Question 4
Which Ollama model should be the default in docs/examples?

A) `qwen2.5:7b`
B) `mistral:7b`
C) `llama3.1:8b`
X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 5
How strict should analysis schema validation be on model output?

A) Strict JSON only; reject and retry on invalid output
B) JSON-first; allow fallback parser with best-effort repair
C) Accept markdown/text and transform to schema when possible
X) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question 6
Should user feedback endpoint update future retrieval ranking locally?

A) Yes, persist feedback and use it to boost/deprioritize similar cases
B) Persist feedback only (no ranking effect yet)
C) No persistence for feedback in MVP
X) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question 7
For synthetic datasets, do you prefer deterministic or randomized generation?

A) Deterministic generated files committed to repo (stable demo)
B) Seeded generator script + generated files committed
C) Seeded generator only; data produced at runtime
X) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question 8
Security Extensions
Should security extension rules be enforced for this project?

A) Yes - enforce all SECURITY rules as blocking constraints
B) No - skip all SECURITY rules (PoC/prototype mode)
X) Other (please describe after [Answer]: tag below)

[Answer]: A
