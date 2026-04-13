## Workflow Start
**Timestamp**: 2026-04-02T15:26:55Z
**User Input**: "Role:
You are my senior software architect and lead engineer.

Goal:
Design and build an end-to-end “AI Bug Triage and Resolution Service” integrated with Jira, using a clean, production-style architecture. This is a resume-quality project that demonstrates AI agents working with private organizational-style data and Jira workflows.

High-level product:
- NOT a generic chatbot.
- A service that listens to Jira bug events, gathers related context (historical bugs, sample logs/configs/runbooks), analyzes the issue with an LLM, and returns a structured debugging recommendation for engineers.
- Human-in-the-loop: never auto-close, never auto-deploy, never edit production systems.

Primary user story:
“As an engineer, when a Jira bug is created or updated, I want an AI service that reads the issue, looks up similar past incidents and context, and gives me a structured explanation: what is probably wrong, who should own it, and what to check next.”

Constraints:
- Must be free to run locally.
- Use only open-source / free tools.
- Favor clarity and maintainability over cleverness.
- No paid APIs.
- No actual production automation (read-only plus suggested comments only).

Tech stack (default unless there is a clear reason otherwise):
- Backend: Python 3.11+, FastAPI, Pydantic, Uvicorn.
- AI orchestration: LangGraph OR a simple custom orchestration layer in Python.
- Model: local via Ollama (e.g., Llama, Qwen, Mistral) behind a model service abstraction.
- Storage: SQLite (MVP) with a clean path to PostgreSQL later.
- ORM: SQLAlchemy.
- Retrieval: start WITHOUT vector DB — use keyword search + metadata filters on a synthetic historical bug dataset.
- Frontend: Streamlit dashboard (preferred for speed) OR minimal React if absolutely necessary.
- Tests: Pytest.

External integration:
- Jira Cloud REST API for:
  - Fetch issue by ID.
  - Fetch comments.
  - Optionally fetch attachments metadata.
  - Webhook endpoint for “issue created/updated” events.
  - Post a comment draft back to Jira.
- Use env vars (no hardcoding secrets):
  - JIRA_BASE_URL
  - JIRA_EMAIL or JIRA_USER
  - JIRA_API_TOKEN
  - OLLAMA_BASE_URL
  - MODEL_NAME

System architecture (conceptual layers):
1) API Layer
   - FastAPI endpoints for health, Jira webhooks, analyze-by-ID, get-report, feedback.

2) Ingestion Layer
   - Jira client to fetch issue + comments + metadata.
   - Normalizes into internal Issue schema.

3) Context Layer
   - Loads additional context from:
     - synthetic historical bug dataset,
     - synthetic runbooks/config/log snippets.
   - No real company data.

4) Retrieval Layer
   - Finds similar historical bugs using keyword search + simple scoring (e.g., title, description, error signature, labels, service/env).
   - Return top-N candidates and associated evidence.

5) Analysis Layer (AI reasoning)
   - Given: normalized issue + retrieved similar incidents + evidence.
   - Produces a structured JSON analysis:
     - issue_id
     - summary
     - category (config, runtime, OS mismatch, dependency, infra, deployment regression, code defect, duplicate, insufficient info)
     - severity (e.g., low/medium/high)
     - likely_owner/team (string)
     - confidence (0–1 or 0–100%)
     - possible_root_causes (list of strings)
     - evidence (list: references to historical cases / snippets)
     - similar_issues (list of IDs)
     - recommended_steps (ordered list of debugging actions)
     - missing_information (what engineer should add)
     - jira_comment_draft (human-readable text)
     - created_at

6) Guardrails Layer
   - Always include confidence and mention uncertainty.
   - Mark low-confidence results as “needs human review.”
   - Never claim the bug is fixed.
   - No auto-actions on Jira beyond posting comments/drafts.

7) Output Layer
   - API JSON response.
   - Dashboard view for analysis.
   - Optional Jira comment draft.

Expected inputs:
- Jira issue ID (primary).
- Or full JSON payload from Jira webhook.

Expected outputs:
- Structured JSON analysis object.
- Human-readable report in UI.
- Optional Jira comment content.

Synthetic data requirements:
- Create realistic but fake data:
  - ~100+ historical bugs across services (auth, payments, notifications, search, frontend, etc.).
  - Each with: id, title, summary, error_signature, category, root_cause, resolution, team, environment, severity, created_at, maybe duplicate_of.
  - 10–20 synthetic runbook snippets.
  - 10–20 config issue examples.
  - 10–20 log/error snippets.
- Store in /data as JSON/CSV files.
- Use them for retrieval and demo.

Project structure (example; adapt but keep clear layers):

/app
  /api        # FastAPI routers
  /core       # settings, logging, config
  /models     # SQLAlchemy models
  /schemas    # Pydantic schemas
  /services   # business logic (Jira, analysis, retrieval, datasets)
  /agents     # AI orchestration / prompt logic
  /retrieval  # search/retrieval utilities
  /integrations # Jira client, etc.
  /db         # database init
  main.py

/dashboard
  streamlit_app.py

/data
  historical_bugs.json
  runbooks.json
  configs.json
  logs.json

/tests
/docs

.env.example
README.md
requirements.txt

API endpoints (MVP):
- GET /health
- POST /webhooks/jira
- GET /issues/{issue_id}/analyze
- GET /issues/{issue_id}/report
- POST /feedback

Optional:
- POST /jira/{issue_id}/comment-draft
- GET /search/similar?query=...

AI prompting requirements:
- The model must act as a careful bug triage assistant:
  - Summarize issue.
  - Classify into one category.
  - Identify likely root causes.
  - Use ONLY provided evidence (no external knowledge about the company).
  - Provide a confidence estimate.
  - Recommend specific next debugging steps.
  - Highlight missing information (what extra logs, config, or steps would help).
  - Output structured JSON for the backend plus a natural-language explanation for humans.

Engineering rules:
- Use type hints everywhere.
- Use docstrings for public functions/methods.
- Use clear, consistent logging.
- Keep files focused and not too large.
- Separate HTTP layer (routers) from business logic (services) and from AI logic (agents).
- Follow FastAPI structuring best practices. [web:57][web:60]
- Add tests for core logic (retrieval, analysis pipeline, JSON schema validation).
- Prefer explicit over magical.

Build sequence:
1) Plan and repo structure.
2) Backend skeleton (FastAPI, basic routes, config).
3) Synthetic data + retrieval utilities.
4) Jira client + webhook + issue fetch.
5) Analysis pipeline + AI layer.
6) Persistence of analyses.
7) Streamlit dashboard.
8) Tests for core paths.
9) README + docs.

Working style:
- Before coding each phase, write a short plan.
- Implement the phase, then summarize what you did.
- If architecture tradeoffs appear, choose the simplest production-credible option and explain briefly in comments and docs."
**AI Response**: "Loaded AI-DLC core and extension rules. Started Workspace Detection and requirements workflow."
**Context**: Inception start, user request capture

---
## Unit 2 — Code Generation Complete
**Timestamp**: 2026-04-02T17:15:14Z
**User Input**: "Proceed.

The Unit 2 plan looks good. Go ahead and:
1) generate the synthetic datasets under /data using the seeded script,
2) implement dataset_loader, retrieval schemas, and keyword_retrieval as described,
3) add and run tests in tests/test_retrieval.py,
4) then summarize what you implemented and the test results.

Do not start Unit 3 until I explicitly approve it."
**AI Response**: "Generated deterministic synthetic datasets under `data/`, implemented `app/services/dataset_loader.py`, retrieval schemas (`app/schemas/retrieval.py`), keyword retrieval (`app/retrieval/keyword_retrieval.py`), retrieval backend interface (`app/retrieval/retrieval_backend.py`), and retrieval tests (`tests/test_retrieval.py`). Ran `pytest` successfully (5 passed)."
**Context**: CONSTRUCTION - Unit 2 synthetic datasets + retrieval

---
## Unit 3 — Code Generation Complete
**Timestamp**: 2026-04-08T16:40:06Z
**User Input**: "I approve Unit 2.

You are authorized to start Code Generation for Unit 3 only (Jira integration + normalization).

Instructions:
1. Execute only Unit 3.
2. Before writing code, show the Unit 3 code generation plan with:
   - files to create/modify,
   - responsibilities of each file,
   - the Jira client interface and mock/live behavior,
   - normalization schema design,
   - tests to add,
   - assumptions and deferred items.
3. Then implement Unit 3.
4. Run/build/test whatever is applicable for Unit 3.
5. Summarize:
   - what was completed,
   - files created/modified,
   - test results,
   - what remains for Unit 4.
6. Do not begin Unit 4 until I explicitly approve it.

Important constraints for Unit 3:
- No Ollama/model integration yet.
- No JSON repair logic yet unless strictly required by a shared schema.
- No SQLite persistence yet.
- No Streamlit.
- Jira integration must support:
  - env-driven live mode,
  - mock fallback mode,
  - issue fetch by ID,
  - comments/metadata retrieval,
  - webhook payload parsing readiness as needed for this unit.
- Normalize Jira issue data into a clean internal schema with typed Pydantic models.
- Keep the integration and normalization layers easy to test independently."
**AI Response**: "Created Unit 3 plan, implemented Jira client (live/mock), webhook key parser, raw/normalized schemas, issue normalizer, fixtures and tests; ran pytest successfully."
**Context**: CONSTRUCTION - Unit 3 Jira integration + normalization

---
## Unit 4 — Code Generation Complete
**Timestamp**: 2026-04-08T16:45:15Z
**User Input**: "I approve Unit 3.

You are authorized to start Code Generation for Unit 4 only (Ollama/model abstraction + analysis orchestration + JSON-first output with repair fallback).

Instructions:
1. Execute only Unit 4.
2. Before writing code, show the Unit 4 code generation plan with:
   - files to create/modify,
   - responsibilities of each file,
   - model service abstraction design,
   - analysis output schema design,
   - orchestration flow,
   - JSON validation / repair fallback approach,
   - tests to add,
   - assumptions and deferred items.
3. Then implement Unit 4.
4. Run/build/test whatever is applicable for Unit 4.
5. Summarize:
   - what was completed,
   - files created/modified,
   - test results,
   - what remains for Unit 5.
6. Do not begin Unit 5 until I explicitly approve it.

Important constraints for Unit 4:
- No SQLite persistence yet.
- No Streamlit.
- No webhook endpoint implementation yet unless strictly needed by shared analysis wiring.
- Keep Ollama access behind a clean model service abstraction.
- Default model should remain qwen2.5:7b, configurable via env vars.
- Prefer structured JSON output via Ollama’s structured output support when possible.
- Validate model output against Pydantic schemas.
- If parsing fails, use a repair fallback and record diagnostics cleanly.
- Keep analysis human-in-the-loop: confidence, uncertainty, and no “issue fixed” claims.
- Keep the orchestration custom and LangGraph-ready, not LangGraph-first."
**AI Response**: "Created Unit 4 plan and implemented analysis schema, model abstraction, prompts, orchestrator, JSON repair fallback, and tests. Executed pytest successfully."
**Context**: CONSTRUCTION - Unit 4 model abstraction + orchestration

---
## Unit 5 — Code Generation Complete
**Timestamp**: 2026-04-08T16:53:29Z
**User Input**: "I approve Unit 4.

You are authorized to start Code Generation for Unit 5 only (SQLite persistence + API wiring + orchestration integration).

Instructions:
1. Execute only Unit 5.
2. Before writing code, show the Unit 5 code generation plan with:
   - files to create/modify,
   - responsibilities of each file,
   - SQLite/SQLAlchemy model design,
   - API route wiring for analyze, report, webhook, and feedback,
   - how orchestration ties into the API flow,
   - tests to add,
   - assumptions and deferred items.
3. Then implement Unit 5.
4. Run/build/test whatever is applicable for Unit 5.
5. Summarize:
   - what was completed,
   - files created/modified,
   - test results,
   - what remains for Unit 6.
6. Do not begin Unit 6 until I explicitly approve it.

Important constraints for Unit 5:
- SQLite only (no PostgreSQL yet).
- Keep the DB layer behind a clean repository/store abstraction for future PostgreSQL migration.
- Wire these API routes fully:
  - POST /webhooks/jira
  - GET /issues/{issue_id}/analyze
  - GET /issues/{issue_id}/report
  - POST /feedback
- Orchestration should integrate cleanly: fetch issue → normalize → retrieve → analyze → persist → return report.
- Feedback persistence is storage-only (no retrieval reranking effect yet).
- No Streamlit yet.
- Keep security rules active: validate all incoming payloads, no sensitive data in logs.
- Handle errors gracefully: missing issue, failed Jira fetch, model timeout, invalid feedback payload."
**AI Response**: "Created Unit 5 plan, implemented SQLite persistence layer with store abstractions, wired API routes, integrated triage orchestration path, added API and persistence tests, and ran full pytest successfully."
**Context**: CONSTRUCTION - Unit 5 persistence + API wiring + integration

---
## Unit 6 + Unit 7 — Back-to-Back Execution Complete
**Timestamp**: 2026-04-08T17:05:22Z
**User Input**: "I approve Unit 5.

You are authorized to execute Unit 6 and Unit 7 back to back in this single session.

Complete Unit 6 fully first, then immediately proceed to Unit 7 without waiting for approval between them.

---

UNIT 6 — Quality + Docs

Instructions:
1. Show the Unit 6 code generation plan (files, scope, test additions, doc targets).
2. Implement Unit 6:
   - Expand Pytest coverage:
     - retrieval edge cases (no match, partial match, score tie-breaking)
     - pipeline error paths (Jira 502, model 504, missing issue)
     - JSON repair fallback paths
     - feedback persistence
     - schema guardrail enforcement
   - Write the full README.md covering:
     - what the project is and why it matters
     - architecture overview with ASCII diagram
     - tech stack
     - local setup and run instructions
     - environment variables reference
     - how to configure Jira integration (live and mock mode)
     - how to set up and run Ollama with qwen2.5:7b
     - how the triage pipeline works end to end
     - API endpoints with example curl requests and responses
     - synthetic dataset description
     - limitations
     - future improvements
   - Add a short SECURITY.md with:
     - no hardcoded credentials
     - env var usage
     - human-in-the-loop policy
     - no autonomous production actions
   - Add a short ARCHITECTURE.md with:
     - layer descriptions
     - data flow
     - module responsibilities
3. Run full pytest suite and confirm all pass.
4. Summarize Unit 6 completion, then immediately proceed to Unit 7.

Constraints for Unit 6:
- No Streamlit yet.
- Do not change any existing implementation logic.
- Only add tests and documentation.

---

UNIT 7 — Streamlit Dashboard (last unit)

Instructions:
1. Show the Unit 7 code generation plan (files, UI sections, backend calls).
2. Implement the Streamlit dashboard in dashboard/streamlit_app.py:
   - Header section:
     - project name and short description
     - backend health status indicator (calls GET /health)
     - configurable backend URL at top of file via env or constant
   - Analyze Issue panel:
     - text input for Jira issue ID
     - Analyze button
     - calls GET /issues/{issue_id}/analyze
     - displays structured result clearly:
       - summary
       - category and severity as labels/badges
       - confidence as a progress bar or colored indicator
       - likely owner team
       - similar issues list
       - recommended steps as a numbered list
       - missing information section
       - jira comment draft as a copyable text area
       - needs_human_review warning if flagged
   - Past Analyses section:
     - shows list of previously analyzed issues via GET /issues/{issue_id}/report or a suitable endpoint
     - clicking one loads its full report
   - Feedback panel:
     - helpful / not helpful buttons for the current analysis
     - optional comment field
     - submits POST /feedback
     - shows confirmation on success
   - Error handling:
     - show user-friendly messages for backend errors
     - do not expose raw stack traces
3. Summarize Unit 7 completion with files created and final project status.

Constraints for Unit 7:
- Keep Streamlit UI clean and functional, not over-designed.
- All backend URLs configurable at top of file.
- Handle backend being offline gracefully.
- No authentication needed for MVP.

---

After both units are done, provide a final project completion summary:
- all units completed,
- total test count,
- how to run the backend,
- how to run the dashboard,
- what to demo."
**AI Response**: "Executed Unit 6 and Unit 7 back-to-back: added expanded tests and full docs, implemented Streamlit dashboard, verified pytest pass, and verified Streamlit dependency installation."
**Context**: CONSTRUCTION - Units 6 and 7 completion

---
## Workspace Detection
**Timestamp**: 2026-04-02T15:26:55Z
**User Input**: "Role:
You are my senior software architect and lead engineer.

Goal:
Design and build an end-to-end “AI Bug Triage and Resolution Service” integrated with Jira, using a clean, production-style architecture. This is a resume-quality project that demonstrates AI agents working with private organizational-style data and Jira workflows.

High-level product:
- NOT a generic chatbot.
- A service that listens to Jira bug events, gathers related context (historical bugs, sample logs/configs/runbooks), analyzes the issue with an LLM, and returns a structured debugging recommendation for engineers.
- Human-in-the-loop: never auto-close, never auto-deploy, never edit production systems.

Primary user story:
“As an engineer, when a Jira bug is created or updated, I want an AI service that reads the issue, looks up similar past incidents and context, and gives me a structured explanation: what is probably wrong, who should own it, and what to check next.”

Constraints:
- Must be free to run locally.
- Use only open-source / free tools.
- Favor clarity and maintainability over cleverness.
- No paid APIs.
- No actual production automation (read-only plus suggested comments only)."
**AI Response**: "Workspace scanned as Greenfield. Reverse engineering skipped. Proceeding to Requirements Analysis."
**Context**: INCEPTION - Workspace Detection complete

---

## Requirements Analysis
**Timestamp**: 2026-04-02T15:26:55Z
**User Input**: "using AI-DLC I want to implement a new Bug Resolving Tool. How do you reccomend I build it, ask question to know more what I want to build."
**AI Response**: "Created requirements clarification questions file including extension applicability question."
**Context**: INCEPTION - Requirements Analysis Step 6 question generation

---

## Requirements Analysis
**Timestamp**: 2026-04-02T16:03:37Z
**User Input**: "Important implementation preferences:
- Backend first
- Real Jira integration with env vars + fallback mocks
- Custom orchestration now, but keep it LangGraph-ready
- Default Ollama model: qwen2.5:7b
- JSON-first output with repair fallback
- Persist feedback only in MVP
- Seeded synthetic dataset generator plus committed generated files
- Enforce security rules
- SQLite for MVP
- No vector DB in MVP
- Streamlit dashboard after backend
- No autonomous fixes or production actions"
**AI Response**: "Validated question answers, generated finalized requirements document, enabled security extension, and prepared approval gate."
**Context**: INCEPTION - Requirements Analysis completion draft

---

## Requirements Analysis
**Timestamp**: 2026-04-02T16:29:27Z
**User Input**: "I reviewed the requirements and approve them.

Proceed to User Stories.

Important instructions for the next step:
1. Group user stories by phase.
2. Separate backend MVP stories from later Streamlit/dashboard stories.
3. Add acceptance criteria for each story.
4. Show dependencies between stories.
5. Keep all previously approved constraints unchanged.
6. After generating the user stories, propose implementation units and wait for my approval before writing code."
**AI Response**: "Generated personas, phased user stories (backend MVP vs dashboard), dependency table, assessment and story plan artifacts; created implementation-units-proposal.md; awaiting approval before implementation."
**Context**: INCEPTION - User Stories generation and implementation units proposal

---

## User Stories Approval
**Timestamp**: 2026-04-02T16:43:18Z
**User Input**: "Approve.

I approve the user stories and implementation units.

Proceed to Workflow Planning, but do not generate code yet.

During workflow planning:
- show unit-by-unit execution order,
- list expected files created or modified per unit,
- list test scope per unit,
- identify any optional items that can be deferred,
- keep backend-first and Streamlit-last,
- wait for my explicit approval before code generation."
**AI Response**: "Created execution-plan.md with unit order, files, tests, deferrals; updated state; workflow planning completion pending user approval of execution plan before code."
**Context**: INCEPTION - Workflow Planning artifact generation

---

## Workflow Planning - Approval Prompt
**Timestamp**: 2026-04-02T16:43:18Z
**AI Prompt**: "Please review aidlc-docs/inception/plans/execution-plan.md and approve or request changes. Code generation will not begin until you explicitly approve."
**User Response**: "[Pending]"
**Status**: Pending
**Context**: Awaiting execution plan approval before Code Planning / Unit 1

---

## Workflow Planning - Approval
**Timestamp**: 2026-04-02T17:04:00Z
**User Input**: "I approve the execution plan.

Authorize Code Generation for Unit 1 only.

Constraints:
- Do not start Unit 2 without my approval.
- Keep implementation aligned with the approved requirements and user stories.
- Keep code in the workspace root/project files, and documentation only in aidlc-docs where appropriate.
- Follow backend-first sequencing exactly.

For Unit 1:
1. show the detailed code generation plan first,
2. wait for my acknowledgement if needed,
3. then implement,
4. then run tests/checks,
5. then provide a concise completion report."
**AI Response**: "Created aidlc-docs/construction/unit-1/code-generation-plan.md; implemented Unit 1 app shell, health, settings, tests; ran pytest (1 passed); Unit 2 not started."
**Status**: Approved for Unit 1 only
**Context**: CONSTRUCTION - Code Generation Unit 1

---

## Unit 2 — Code Generation Plan Presented
**Timestamp**: 2026-04-02T17:07:47Z
**User Input**: "I approve Unit 1.

You are authorized to start Code Generation for Unit 2 only (synthetic data + retrieval).

Instructions:
1. Execute only Unit 2.
2. Before writing code, show the Unit 2 code generation plan with:
   - files to create/modify,
   - responsibilities of each file,
   - dataset files to generate,
   - retrieval logic/scoring approach,
   - tests to add,
   - assumptions and deferred items.
3. Then implement Unit 2.
4. Generate the seeded synthetic datasets and commit-ready files required for this unit.
5. Run/build/test whatever is applicable for this unit 2.
6. Summarize:
   - what was completed,
   - what files were created/modified,
   - test results,
   - what remains for Unit 3.
7. Do not begin Unit 3 until I explicitly approve it.

Important constraints for Unit 2:
- No Jira client yet beyond what Unit 2 strictly needs.
- No Ollama/model integration yet.
- No SQLite persistence yet.
- No Streamlit.
- Retrieval must be keyword + metadata only, no vector DB.
- Keep the retrieval design extensible for future semantic search.
- Use deterministic, seeded synthetic data generation plus committed generated dataset files."
**AI Response**: "Created Unit 2 code-generation plan at `aidlc-docs/construction/unit-2/code-generation-plan.md` and will wait for your explicit acknowledgement before generating datasets or writing any Unit 2 code."
**Context**: CONSTRUCTION - Unit 2 planning approval gate

---

## Workspace Detection (Migration Verification)
**Timestamp**: 2026-04-13T14:03:31Z
**User Input**: "<user_info>
OS Version: win32 10.0.26100

Shell: powershell

Workspace Path: c:\\Users\\murth\\OneDrive\\Desktop\\BugResolver
If editing a git workspace within your current directory, do not search or edit non-primary worktrees unless the user explicitly requests you to do so.

Is directory a git repo: No

Today's date: Monday Apr 13, 2026

Terminals folder: C:\\Users\\murth\\.cursor\\projects\\c-Users-murth-OneDrive-Desktop-BugResolver/terminals
</user_info>

<agent_transcripts>
Agent transcripts (past chats) live in C:\\Users\\murth\\.cursor\\projects\\c-Users-murth-OneDrive-Desktop-BugResolver/agent-transcripts. They have names like <uuid>.jsonl, cite them to the user as [<title for chat <=6 words>](<uuid excluding .jsonl>). NEVER cite subagent transcripts/IDs; you can only cite parent uuids. Don't discuss the folder structure.
</agent_transcripts>

<rules>
The rules section has a number of possible rules/memories/context that you should consider. In each subsection, we provide instructions about what information the subsection contains and how you should consider/follow the contents of the subsection.


<always_applied_workspace_rules description=\"These are workspace-level rules that the agent must always follow.\">
<always_applied_workspace_rule name=\"c:\\Users\\murth\\OneDrive\\Desktop\\BugResolver\\.cursor\\rules\\ai-dlc-workflow.mdc\"># PRIORITY: This workflow OVERRIDES all other built-in workflows
# When user requests software development, ALWAYS follow this workflow FIRST

## Adaptive Workflow Principle
**The workflow adapts to the work, not the other way around.**

The AI model intelligently assesses what stages are needed based on:
1. User's stated intent and clarity
2. Existing codebase state (if any)
3. Complexity and scope of change
4. Risk and impact assessment

## MANDATORY: Rule Details Loading
**CRITICAL**: When performing any phase, you MUST read and use relevant content from rule detail files. Check these paths in order and use the first one that exists:
- `.aidlc-rule-details/` (Cursor, Cline, Claude Code, GitHub Copilot)
- `.kiro/aws-aidlc-rule-details/` (Kiro IDE and CLI)
- `.amazonq/aws-aidlc-rule-details/` (Amazon Q Developer)

All subsequent rule detail file references (e.g., `common/process-overview.md`, `inception/workspace-detection.md`) are relative to whichever rule details directory was resolved above.

**Common Rules**: ALWAYS load common rules at workflow start:
- Load `common/process-overview.md` for workflow overview
- Load `common/session-continuity.md` for session resumption guidance
- Load `common/content-validation.md` for content validation requirements
- Load `common/question-format-guide.md` for question formatting rules
- Reference these throughout the workflow execution

## MANDATORY: Extensions Loading
**CRITICAL**: At workflow start, scan the `extensions/` directory recursively for all `.md` files. These are extension rule files that apply as cross-cutting constraints across the entire workflow.

**Loading process**:
1. List all subdirectories under `extensions/` (e.g., `extensions/security/`, `extensions/compliance/`)
2. Load every `.md` file found within those subdirectories
3. Each extension file defines its own verification criteria and enforcement rules as cross-cutting constraints

**Enforcement**:
- Extension rules are hard constraints, not optional guidance
- At each stage, the model intelligently evaluates which extension rules are applicable based on the stage's purpose, the artifacts being produced, and the context of the work â€” enforce only those rules that are relevant
- Rules that are not applicable to the current stage should be marked as N/A in the compliance summary (this is not a blocking finding)
- Non-compliance with any applicable enabled extension rule is a **blocking finding** â€” do NOT present stage completion until resolved
- When presenting stage completion, include a summary of extension rule compliance (compliant/non-compliant/N/A per rule, with brief rationale for N/A determinations)

**Conditional Enforcement**: Extensions may be conditionally enabled/disabled. See `inception/requirements-analysis.md` for the collection mechanism. Before enforcing any extension at ANY stage, check its `Enabled` status in `aidlc-docs/aidlc-state.md` under `## Extension Configuration`. Skip disabled extensions and log the skip in audit.md. Default to enforced if no configuration exists. Extensions without an `## Applicability Question` are always enforced.

## MANDATORY: Content Validation
**CRITICAL**: Before creating ANY file, you MUST validate content according to `common/content-validation.md` rules:
- Validate Mermaid diagram syntax
- Validate ASCII art diagrams (see `common/ascii-diagram-standards.md`)
- Escape special characters properly
- Provide text alternatives for complex visual content
- Test content parsing compatibility

## MANDATORY: Question File Format
**CRITICAL**: When asking questions at any phase, you MUST follow question format guidelines.

**See `common/question-format-guide.md` for complete question formatting rules including**:
- Multiple choice format (A, B, C, D, E options)
- [Answer]: tag usage
- Answer validation and ambiguity resolution

## MANDATORY: Custom Welcome Message
**CRITICAL**: When starting ANY software development request, you MUST display the welcome message.

**How to Display Welcome Message**:
1. Load the welcome message from `common/welcome-message.md` (in the resolved rule details directory)
2. Display the complete message to the user
3. This should only be done ONCE at the start of a new workflow
4. Do NOT load this file in subsequent interactions to save context space

# Adaptive Software Development Workflow

---

# INCEPTION PHASE

**Purpose**: Planning, requirements gathering, and architectural decisions

**Focus**: Determine WHAT to build and WHY

**Stages in INCEPTION PHASE**:
- Workspace Detection (ALWAYS)
- Reverse Engineering (CONDITIONAL - Brownfield only)
- Requirements Analysis (ALWAYS - Adaptive depth)
- User Stories (CONDITIONAL)
- Workflow Planning (ALWAYS)
- Application Design (CONDITIONAL)
- Units Generation (CONDITIONAL)

---

## Workspace Detection (ALWAYS EXECUTE)

1. **MANDATORY**: Log initial user request in audit.md with complete raw input
2. Load all steps from `inception/workspace-detection.md`
3. Execute workspace detection:
 - Check for existing aidlc-state.md (resume if found)
 - Scan workspace for existing code
 - Determine if brownfield or greenfield
 - Check for existing reverse engineering artifacts
4. Determine next phase: Reverse Engineering (if brownfield and no artifacts) OR Requirements Analysis
5. **MANDATORY**: Log findings in audit.md
6. Present completion message to user (see workspace-detection.md for message formats)
7. Automatically proceed to next phase

## Reverse Engineering (CONDITIONAL - Brownfield Only)

**Execute IF**:
- Existing codebase detected
- No previous reverse engineering artifacts found

**Skip IF**:
- Greenfield project
- Previous reverse engineering artifacts exist

**Execution**:
1. **MANDATORY**: Log start of reverse engineering in audit.md
2. Load all steps from `inception/reverse-engineering.md`
3. Execute reverse engineering:
 - Analyze all packages and components
 - Generate a business overview of the whole system covering the business transactions
 - Generate architecture documentation
 - Generate code structure documentation
 - Generate API documentation
 - Generate component inventory
 - Generate Interaction Diagrams depicting how business transactions are implemented across components
 - Generate technology stack documentation
 - Generate dependencies documentation

4. **Wait for Explicit Approval**: Present detailed completion message (see reverse-engineering.md for message format) - DO NOT PROCEED until user confirms
5. **MANDATORY**: Log user's response in audit.md with complete raw input

## Requirements Analysis (ALWAYS EXECUTE - Adaptive Depth)

**Always executes** but depth varies based on request clarity and complexity:
- **Minimal**: Simple, clear request - just document intent analysis
- **Standard**: Normal complexity - gather functional and non-functional requirements
- **Comprehensive**: Complex, high-risk - detailed requirements with traceability

**Execution**:
1. **MANDATORY**: Log any user input during this phase in audit.md
2. Load all steps from `inception/requirements-analysis.md`
3. Execute requirements analysis:
 - Load reverse engineering artifacts (if brownfield)
 - Analyze user request (intent analysis)
 - Determine requirements depth needed
 - Assess current requirements
 - Ask clarifying questions (if needed)
 - Generate requirements document
4. Execute at appropriate depth (minimal/standard/comprehensive)
5. **Wait for Explicit Approval**: Follow approval format from requirements-analysis.md detailed steps - DO NOT PROCEED until user confirms
6. **MANDATORY**: Log user's response in audit.md with complete raw input

## User Stories (CONDITIONAL)

**INTELLIGENT ASSESSMENT**: Use multi-factor analysis to determine if user stories add value:

**ALWAYS Execute IF** (High Priority Indicators):
- New user-facing features or functionality
- Changes affecting user workflows or interactions
- Multiple user types or personas involved
- Complex business requirements with acceptance criteria needs
- Cross-functional team collaboration required
- Customer-facing API or service changes
- New product capabilities or enhancements

**LIKELY Execute IF** (Medium Priority - Assess Complexity):
- Modifications to existing user-facing features
- Backend changes that indirectly affect user experience
- Integration work that impacts user workflows
- Performance improvements with user-visible benefits
- Security enhancements affecting user interactions
- Data model changes affecting user data or reports

**COMPLEXITY-BASED ASSESSMENT**: For medium priority cases, execute user stories if:
- Request involves multiple components or services
- Changes span multiple user touchpoints
- Business logic is complex or has multiple scenarios
- Requirements have ambiguity that stories could clarify
- Implementation affects multiple user journeys
- Change has significant business impact or risk

**SKIP ONLY IF** (Low Priority - Simple Cases):
- Pure internal refactoring with zero user impact
- Simple bug fixes with clear, isolated scope
- Infrastructure changes with no user-facing effects
- Technical debt cleanup with no functional changes
- Developer tooling or build process improvements
- Documentation-only updates

**ASSESSMENT CRITERIA**: When in doubt, favor inclusion of user stories for:
- Requests with business stakeholder involvement
- Changes requiring user acceptance testing
- Features with multiple implementation approaches
- Work that benefits from shared team understanding
- Projects where requirements clarity is valuable

**ASSESSMENT PROCESS**: 
1. Analyze request complexity and scope
2. Identify user impact (direct or indirect)
3. Evaluate business context and stakeholder needs
4. Consider team collaboration benefits
5. Default to inclusion for borderline cases

**Note**: If Requirements Analysis executed, Stories can reference and build upon those requirements.

**User Stories has two parts within one stage**:
1. **Part 1 - Planning**: Create story plan with questions, collect answers, analyze for ambiguities, get approval
2. **Part 2 - Generation**: Execute approved plan to generate stories and personas

**Execution**:
1. **MANDATORY**: Log any user input during this phase in audit.md
2. Load all steps from `inception/user-stories.md`
3. **MANDATORY**: Perform intelligent assessment (Step 1 in user-stories.md) to validate user stories are needed
4. Load reverse engineering artifacts (if brownfield)
5. If Requirements exist, reference them when creating stories
6. Execute at appropriate depth (minimal/standard/comprehensive)
7. **PART 1 - Planning**: Create story plan with questions, wait for user answers, analyze for ambiguities, get approval
8. **PART 2 - Generation**: Execute approved plan to generate stories and personas
9. **Wait for Explicit Approval**: Follow approval format from user-stories.md detailed steps - DO NOT PROCEED until user confirms
10. **MANDATORY**: Log user's response in audit.md with complete raw input

## Workflow Planning (ALWAYS EXECUTE)

1. **MANDATORY**: Log any user input during this phase in audit.md
2. Load all steps from `inception/workflow-planning.md`
3. **MANDATORY**: Load content validation rules from `common/content-validation.md`
4. Load all prior context:
 - Reverse engineering artifacts (if brownfield)
 - Intent analysis
 - Requirements (if executed)
 - User stories (if executed)
5. Execute workflow planning:
 - Determine which phases to execute
 - Determine depth level for each phase
 - Create multi-package change sequence (if brownfield)
 - Generate workflow visualization (VALIDATE Mermaid syntax before writing)
6. **MANDATORY**: Validate all content before file creation per content-validation.md rules
7. **Wait for Explicit Approval**: Present recommendations using language from workflow-planning.md Step 9, emphasizing user control to override recommendations - DO NOT PROCEED until user confirms
8. **MANDATORY**: Log user's response in audit.md with complete raw input

## Application Design (CONDITIONAL)

**Execute IF**:
- New components or services needed
- Component methods and business rules need definition
- Service layer design required
- Component dependencies need clarification

**Skip IF**:
- Changes within existing component boundaries
- No new components or methods
- Pure implementation changes

**Execution**:
1. **MANDATORY**: Log any user input during this phase in audit.md
2. Load all steps from `inception/application-design.md`
3. Load reverse engineering artifacts (if brownfield)
4. Execute at appropriate depth (minimal/standard/comprehensive)
5. **Wait for Explicit Approval**: Present detailed completion message (see application-design.md for message format) - DO NOT PROCEED until user confirms
6. **MANDATORY**: Log user's response in audit.md with complete raw input

## Units Generation (CONDITIONAL)

**Execute IF**:
- System needs decomposition into multiple units of work
- Multiple services or modules required
- Complex system requiring structured breakdown

**Skip IF**:
- Single simple unit
- No decomposition needed
- Straightforward single-component implementation

**Execution**:
1. **MANDATORY**: Log any user input during this phase in audit.md
2. Load all steps from `inception/units-generation.md`
3. Load reverse engineering artifacts (if brownfield)
4. Execute at appropriate depth (minimal/standard/comprehensive)
5. **Wait for Explicit Approval**: Present detailed completion message (see units-generation.md for message format) - DO NOT PROCEED until user confirms
6. **MANDATORY**: Log user's response in audit.md with complete raw input

---

# ðŸŸ¢ CONSTRUCTION PHASE

**Purpose**: Detailed design, NFR implementation, and code generation

**Focus**: Determine HOW to build it

**Stages in CONSTRUCTION PHASE**:
- Per-Unit Loop (executes for each unit):
 - Functional Design (CONDITIONAL, per-unit)
 - NFR Requirements (CONDITIONAL, per-unit)
 - NFR Design (CONDITIONAL, per-unit)
 - Infrastructure Design (CONDITIONAL, per-unit)
 - Code Generation (ALWAYS, per-unit)
- Build and Test (ALWAYS - after all units complete)

**Note**: Each unit is completed fully (design + code) before moving to the next unit.

---

## Per-Unit Loop (Executes for Each Unit)

**For each unit of work, execute the following stages in sequence:**

### Functional Design (CONDITIONAL, per-unit)

**Execute IF**:
- New data models or schemas
- Complex business logic
- Business rules need detailed design

**Skip IF**:
- Simple logic changes
- No new business logic

**Execution**:
1. **MANDATORY**: Log any user input during this stage in audit.md
2. Load all steps from `construction/functional-design.md`
3. Execute functional design for this unit
4. **MANDATORY**: Present standardized 2-option completion message as defined in functional-design.md - DO NOT use emergent 3-option behavior
5. **Wait for Explicit Approval**: User must choose between "Request Changes" or "Continue to Next Stage" - DO NOT PROCEED until user confirms
6. **MANDATORY**: Log user's response in audit.md with complete raw input

### NFR Requirements (CONDITIONAL, per-unit)

**Execute IF**:
- Performance requirements exist
- Security considerations needed
- Scalability concerns present
- Tech stack selection required

**Skip IF**:
- No NFR requirements
- Tech stack already determined

**Execution**:
1. **MANDATORY**: Log any user input during this stage in audit.md
2. Load all steps from `construction/nfr-requirements.md`
3. Execute NFR assessment for this unit
4. **MANDATORY**: Present standardized 2-option completion message as defined in nfr-requirements.md - DO NOT use emergent behavior
5. **Wait for Explicit Approval**: User must choose between "Request Changes" or "Continue to Next Stage" - DO NOT PROCEED until user confirms
6. **MANDATORY**: Log user's response in audit.md with complete raw input

### NFR Design (CONDITIONAL, per-unit)

**Execute IF**:
- NFR Requirements was executed
- NFR patterns need to be incorporated

**Skip IF**:
- No NFR requirements
- NFR Requirements Assessment was skipped

**Execution**:
1. **MANDATORY**: Log any user input during this stage in audit.md
2. Load all steps from `construction/nfr-design.md`
3. Execute NFR design for this unit
4. **MANDATORY**: Present standardized 2-option completion message as defined in nfr-design.md - DO NOT use emergent behavior
5. **Wait for Explicit Approval**: User must choose between "Request Changes" or "Continue to Next Stage" - DO NOT PROCEED until user confirms
6. **MANDATORY**: Log user's response in audit.md with complete raw input

### Infrastructure Design (CONDITIONAL, per-unit)

**Execute IF**:
- Infrastructure services need mapping
- Deployment architecture required
- Cloud resources need specification

**Skip IF**:
- No infrastructure changes
- Infrastructure already defined

**Execution**:
1. **MANDATORY**: Log any user input during this stage in audit.md
2. Load all steps from `construction/infrastructure-design.md`
3. Execute infrastructure design for this unit
4. **MANDATORY**: Present standardized 2-option completion message as defined in infrastructure-design.md - DO NOT use emergent behavior
5. **Wait for Explicit Approval**: User must choose between "Request Changes" or "Continue to Next Stage" - DO NOT PROCEED until user confirms
6. **MANDATORY**: Log user's response in audit.md with complete raw input

### Code Generation (ALWAYS EXECUTE, per-unit)

**Always executes for each unit**

**Code Generation has two parts within one stage**:
1. **Part 1 - Planning**: Create detailed code generation plan with explicit steps
2. **Part 2 - Generation**: Execute approved plan to generate code, tests, and artifacts

**Execution**:
1. **MANDATORY**: Log any user input during this stage in audit.md
2. Load all steps from `construction/code-generation.md`
3. **PART 1 - Planning**: Create code generation plan with checkboxes, get user approval
4. **PART 2 - Generation**: Execute approved plan to generate code for this unit
5. **MANDATORY**: Present standardized 2-option completion message as defined in code-generation.md - DO NOT use emergent behavior
6. **Wait for Explicit Approval**: User must choose between "Request Changes" or "Continue to Next Stage" - DO NOT PROCEED until user confirms
7. **MANDATORY**: Log user's response in audit.md with complete raw input

---

## Build and Test (ALWAYS EXECUTE)

1. **MANDATORY**: Log any user input during this phase in audit.md
2. Load all steps from `construction/build-and-test.md`
3. Generate comprehensive build and test instructions:
 - Build instructions for all units
 - Unit test execution instructions
 - Integration test instructions (test interactions between units)
 - Performance test instructions (if applicable)
 - Additional test instructions as needed (contract tests, security tests, e2e tests)
4. Create instruction files in build-and-test/ subdirectory: build-instructions.md, unit-test-instructions.md, integration-test-instructions.md, performance-test-instructions.md, build-and-test-summary.md
5. **Wait for Explicit Approval**: Ask: "**Build and test instructions complete. Ready to proceed to Operations stage?**" - DO NOT PROCEED until user confirms
6. **MANDATORY**: Log user's response in audit.md with complete raw input

---

# ðŸŸ¡ OPERATIONS PHASE

**Purpose**: Placeholder for future deployment and monitoring workflows

**Focus**: How to DEPLOY and RUN it (future expansion)

**Stages in OPERATIONS PHASE**:
- Operations (PLACEHOLDER)

---

## Operations (PLACEHOLDER)

**Status**: This stage is currently a placeholder for future expansion.

The Operations stage will eventually include:
- Deployment planning and execution
- Monitoring and observability setup
- Incident response procedures
- Maintenance and support workflows
- Production readiness checklists

**Current State**: All build and test activities are handled in the CONSTRUCTION phase.

## Key Principles

- **Adaptive Execution**: Only execute stages that add value
- **Transparent Planning**: Always show execution plan before starting
- **User Control**: User can request stage inclusion/exclusion
- **Progress Tracking**: Update aidlc-state.md with executed and skipped stages
- **Complete Audit Trail**: Log ALL user inputs and AI responses in audit.md with timestamps
 - **CRITICAL**: Capture user's COMPLETE RAW INPUT exactly as provided
 - **CRITICAL**: Never summarize or paraphrase user input in audit log
 - **CRITICAL**: Log every interaction, not just approvals
- **Quality Focus**: Complex changes get full treatment, simple changes stay efficient
- **Content Validation**: Always validate content before file creation per content-validation.md rules
- **NO EMERGENT BEHAVIOR**: Construction phases MUST use standardized 2-option completion messages as defined in their respective rule files. DO NOT create 3-option menus or other emergent navigation patterns.

## MANDATORY: Plan-Level Checkbox Enforcement

### MANDATORY RULES FOR PLAN EXECUTION
1. **NEVER complete any work without updating plan checkboxes**
2. **IMMEDIATELY after completing ANY step described in a plan file, mark that step [x]**
3. **This must happen in the SAME interaction where the work is completed**
4. **NO EXCEPTIONS**: Every plan step completion MUST be tracked with checkbox updates

### Two-Level Checkbox Tracking System
- **Plan-Level**: Track detailed execution progress within each stage
- **Stage-Level**: Track overall workflow progress in aidlc-state.md
- **Update immediately**: All progress updates in SAME interaction where work is completed

## Prompts Logging Requirements
- **MANDATORY**: Log EVERY user input (prompts, questions, responses) with timestamp in audit.md
- **MANDATORY**: Capture user's COMPLETE RAW INPUT exactly as provided (never summarize)
- **MANDATORY**: Log every approval prompt with timestamp before asking the user
- **MANDATORY**: Record every user response with timestamp after receiving it
- **CRITICAL**: ALWAYS append changes to EDIT audit.md file, NEVER use tools and commands that completely overwrite its contents
- **CRITICAL**: Using file writing tools and commands that overwrite contents of the entire audit.md and cause duplication
- Use ISO 8601 format for timestamps (YYYY-MM-DDTHH:MM:SSZ)
- Include stage context for each entry

### Audit Log Format:
```markdown
## [Stage Name or Interaction Type]
**Timestamp**: [ISO timestamp]
**User Input**: \"[Complete raw user input - never summarized]\"
**AI Response**: \"[AI's response or action taken]\"
**Context**: [Stage, action, or decision made]

---
```

### Correct Tool Usage for audit.md

âœ… CORRECT:

1. Read the audit.md file
2. Append/Edit the file to make changes

âŒ WRONG:

1. Read the audit.md file
2. Completely overwrite the audit.md with the contents of what you read, plus the new changes you want to add to it

## Directory Structure

```text
<WORKSPACE-ROOT>/ # âš ï¸ APPLICATION CODE HERE
â”œâ”€â”€ [project-specific structure] # Varies by project (see code-generation.md)
â”‚
â”œâ”€â”€ aidlc-docs/ # ðŸ“„ DOCUMENTATION ONLY
â”‚ â”œâ”€â”€ inception/ # ðŸ”µ INCEPTION PHASE
â”‚ â”‚ â”œâ”€â”€ plans/
â”‚ â”‚ â”œâ”€â”€ reverse-engineering/ # Brownfield only
â”‚ â”‚ â”œâ”€â”€ requirements/
â”‚ â”‚ â”œâ”€â”€ user-stories/
â”‚ â”‚ â””â”€â”€ application-design/
â”‚ â”œâ”€â”€ construction/ # ðŸŸ¢ CONSTRUCTION PHASE
â”‚ â”‚ â”œâ”€â”€ plans/
â”‚ â”‚ â”œâ”€â”€ {unit-name}/
â”‚ â”‚ â”‚ â”œâ”€â”€ functional-design/
â”‚ â”‚ â”‚ â”œâ”€â”€ nfr-requirements/
â”‚ â”‚ â”‚ â”œâ”€â”€ nfr-design/
â”‚ â”‚ â”‚ â”œâ”€â”€ infrastructure-design/
â”‚ â”‚ â”‚ â””â”€â”€ code/ # Markdown summaries only
â”‚ â”‚ â””â”€â”€ build-and-test/
â”‚ â”œâ”€â”€ operations/ # ðŸŸ¡ OPERATIONS PHASE (placeholder)
â”‚ â”œâ”€â”€ aidlc-state.md
â”‚ â””â”€â”€ audit.md
```

**CRITICAL RULE**:
- Application code: Workspace root (NEVER in aidlc-docs/)
- Documentation: aidlc-docs/ only
- Project structure: See code-generation.md for patterns by project type</always_applied_workspace_rule>
</always_applied_workspace_rules>
</rules>

<open_and_recently_viewed_files>
User currently doesn't have any open files in their IDE.

Note: these files may or may not be relevant to the current conversation. Use the read file tool if you need to get the contents of some of them.
</open_and_recently_viewed_files><user_query>
You are being onboarded to an existing project on a new machine and Cursor account.

The project has already been fully built and should be complete. All source files have 
been migrated from another machine. Your job is to:

1. Understand what exists
2. Verify the migration is complete and correct
3. Set up the environment on this new machine
4. Run tests to confirm everything works
5. Report any issues and fix them

---

STEP 1 — PROJECT CONTEXT

This project is called: AI Bug Triage and Resolution Service.

It is a local-first FastAPI service that:
- Integrates with Jira (live mode via env vars, mock mode as fallback)
- Loads synthetic historical bug data from /data
- Uses keyword + metadata retrieval to find similar past incidents
- Analyzes bugs using a local LLM via Ollama (qwen2.5:7b default)
- Returns structured JSON analysis with confidence, root causes, recommended steps,
  likely owner team, similar issues, and guardrails
- Persists results and feedback in SQLite
- Has a Streamlit dashboard at dashboard/streamlit_app.py

The project was built using the AI-DLC methodology in 7 sequential units:
- Unit 1: FastAPI foundation + health endpoint
- Unit 2: Synthetic dataset generator + keyword/metadata retrieval
- Unit 3: Jira client (live + mock) + issue normalization
- Unit 4: Ollama model abstraction + analysis orchestration + JSON repair
- Unit 5: SQLite persistence + full API route wiring + triage pipeline
- Unit 6: Test hardening + README + SECURITY.md + ARCHITECTURE.md
- Unit 7: Streamlit dashboard

It had 33 passing tests at the end of the original build.

There is also a DEMO_MODE feature (DEMO_MODE=true in .env) that returns a 
realistic hardcoded analysis result when Ollama is not available.

---

STEP 2 — VERIFY MIGRATION COMPLETENESS

Please audit the workspace now and verify the following files and folders exist:

Core backend:
- app/main.py
- app/core/config.py
- app/core/logging.py
- app/api/health.py
- app/api/issues.py
- app/api/webhooks.py
- app/api/feedback.py
- app/api/deps.py
- app/schemas/retrieval.py
- app/schemas/jira.py
- app/schemas/issue.py
- app/schemas/analysis.py
- app/schemas/api.py
- app/services/dataset_loader.py
- app/services/issue_normalizer.py
- app/services/analysis_store.py
- app/services/feedback_store.py
- app/services/triage_pipeline.py
- app/services/json_repair.py
- app/agents/model_client.py
- app/agents/orchestrator.py
- app/agents/prompts.py
- app/retrieval/keyword_retrieval.py
- app/retrieval/retrieval_backend.py
- app/integrations/jira_client.py
- app/db/base.py
- app/db/session.py
- app/models/analysis.py
- app/models/feedback.py

Data:
- data/historical_bugs.json (should have 120+ records)
- data/runbooks.json (should have ~20 records)
- data/configs.json (should have ~15 records)
- data/logs.json (should have ~15 records)
- scripts/generate_synthetic_data.py

Tests:
- tests/conftest.py
- tests/test_health.py
- tests/test_retrieval.py
- tests/test_jira_client_mock.py
- tests/test_normalize_issue.py
- tests/test_analysis_schema.py
- tests/test_orchestrator.py
- tests/test_api_issues.py
- tests/test_persistence.py
- tests/test_retrieval_edges.py
- tests/test_pipeline_errors.py
- tests/test_json_repair_edges.py
- tests/test_feedback_persistence_extra.py
- tests/test_guardrails_extra.py
- tests/fixtures/jira_issue_rest_sample.json
- tests/fixtures/jira_webhook_sample.json

Dashboard:
- dashboard/streamlit_app.py

Config and docs:
- requirements.txt
- .env.example
- pytest.ini
- README.md
- SECURITY.md
- ARCHITECTURE.md
- .gitignore

AI-DLC docs:
- aidlc-docs/aidlc-state.md
- aidlc-docs/inception/requirements/requirements.md

For each missing file, note it clearly.
For each present file, confirm it looks structurally correct (not empty, not corrupted).

---

STEP 3 — ENVIRONMENT SETUP

Set up the environment on this new machine:

1. Create a virtual environment:
   python -m venv venv

2. Activate it:
   - Windows: venv\\Scripts\\activate
   - Mac/Linux: source venv/bin/activate

3. Install dependencies:
   pip install -r requirements.txt

4. Create .env from .env.example:
   Copy .env.example to .env
   Set DEMO_MODE=true so the project works without Ollama for now

5. Report any dependency installation errors clearly.

---

STEP 4 — RUN TESTS

Run the full test suite:
   py -m pytest   (or python -m pytest depending on the system)

Report:
- Total tests found
- Total passed
- Total failed
- Any error messages for failing tests

Expected result: 33 tests passing.

If fewer than 33 pass, investigate and fix any issues caused by the migration
(missing files, broken imports, path issues, missing dependencies, etc.)

---

STEP 5 — SMOKE TEST THE BACKEND

Start the backend:
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

Then verify:
- GET /health returns a valid JSON response
- Report the response content

---

STEP 6 — REPORT

Provide a clear migration report with:

1. Migration status:
   - List any missing files
   - List any files that appear empty or corrupted
   - Overall migration verdict: Complete / Incomplete

2. Environment status:
   - Python version
   - All dependencies installed: Yes / No
   - Any installation issues

3. Test results:
   - Tests passed: X / 33
   - Any failures and their root cause

4. Backend smoke test:
   - /health response

5. Issues found and fixed (if any)

6. What is ready to continue:
   - Backend functional: Yes / No
   - Tests passing: Yes / No
   - Dashboard runnable: Yes / No

---

Do not start any new feature work until this migration verification is complete
and the test suite is passing at the same level as before (33 tests).

If everything is clean, say: \"Migration verified. Ready to continue.\"
If there are issues, fix them and then say: \"Issues resolved. Ready to continue.\"
</user_query>"
**AI Response**: "Loaded AI-DLC workflow and security extension rules. Beginning migration audit, environment setup, test run, and backend smoke test."
**Context**: Migration verification onboarding on new machine

---
