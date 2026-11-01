# Codex Orchestrator Guide: Gemini Delegation Protocol

This document defines the operating protocol for Codex as orchestrator and Gemini as implementation agent via `scripts/delegate.py`.

## Roles & Responsibilities
- **Codex (Orchestrator & Reviewer)**: Plans tasks, secures owner approval per `AGENTS.md`, creates task specifications, executes the delegation wrapper, inspects diffs and test results, and commits accepted changes.
- **Gemini (Implementation Agent)**: Reads context, implements minimal edits strictly within Allowed Paths, avoids running terminal commands or nested agents, and provides a concise report (<= 15 lines).

## Workflow

### 1. Planning & Approval
- Formulate a 3-7 item plan in `plans/PLAN-LIVE.md` specifying precise Allowed Paths for the subtask.
- Wait for owner "ok" before initiating code modifications per `AGENTS.md`.
- Future tasks require precise plan Allowed Paths; the delegation wrapper is an execution convenience, not a security boundary.
- Enforce a maximum of 3 implementation iterations total per subtask.

### 2. Task Authoring
- Create `.delegation/tasks/<TASK-ID>.md` using the structure from `.delegation/TEMPLATE.md`.
- Ensure explicit context paths, step-by-step instructions, strict Allowed Paths, and acceptance tests are documented.

### 3. Launching the Wrapper
- Execute the wrapper from repository root:
  ```bash
  python scripts/delegate.py <TASK-ID> [--timeout SECONDS] [--model MODEL]
  ```
- Defaults: timeout = 900 seconds, model = `gemini-3.8-flash-low`; override the model explicitly for harder tasks.
- No API keys are required; authentication is handled locally via the `agy` CLI subscription.
- No Claude configuration is required.

### 4. Output Review & Scoped Diffs
- The wrapper prints the process return code, log path (`.delegation/logs/<TASK-ID>.log`), and the last 30 lines of output.
- Limit log reads to the tail; do not ingest entire long logs unless debugging failures.
- Check workspace status: `git status --short` and review any untracked files.
- Inspect overall diff statistics: `git diff --stat`.
- Inspect scoped diffs strictly against Allowed Paths: `git diff <allowed paths>`.
- Verify no forbidden files (`tests/`, `schemas/`, Telegram, 3D/CAD) were touched.

### 5. Verification & Iteration
- Codex executes verification tests directly with raw output:
  ```bash
  python -m unittest discover tests
  ```
- If verification fails or adjustments are required:
  - Formulate a focused correction task in `.delegation/tasks/` referencing the failures.
  - Re-run `scripts/delegate.py`.
  - Enforce a maximum of 3 implementation iterations per subtask, including the initial implementation.

### 6. Acceptance & Commit
- Once tests pass (exit code 0) and diffs match intent:
  - Stage only intended files: `git add <files>`.
  - Commit accepted subtask with a descriptive commit message.
  - Update `HANDOFF.md` (at most 25 lines) and advance `plans/PLAN-LIVE.md`.

## Security & Operational Boundaries
- **Not a Security Sandbox**: `agy --mode accept-edits` approves file modifications automatically, but terminal command permissions remain and no OS-level sandbox is provided on the host. Prompts strictly forbid the implementation agent from executing terminal commands.
- **Test Oracle Ownership**: `tests/` and `schemas/` remain immutable contracts owned only by the human. Gemini and Codex must never modify them without explicit owner approval.
