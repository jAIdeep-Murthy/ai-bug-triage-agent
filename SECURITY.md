# SECURITY

## Credentials and secrets

- No hardcoded credentials are allowed.
- Configuration uses environment variables from `.env` / system env.
- `.env.example` provides key names only.

## Human-in-the-loop policy

- This system provides triage recommendations only.
- It does not auto-close issues, auto-deploy fixes, or modify production systems.
- Low-confidence results are marked for human review.

## Production action policy

- No autonomous production actions are performed in this MVP.
- Jira integration is read-oriented for issue/comment retrieval in analysis flow.

## Logging and data handling

- Avoid sensitive token/secret output in logs.
- Use structured, minimal logs for operability and debugging.
