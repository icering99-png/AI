# Task: [TASK-ID] — [Short Task Title]

## Goal
[State the exact goal of this delegation task clearly in 1-3 sentences.]

## Context Paths
[List concrete relative file paths that Gemini must read for context before making changes.]
- `path/to/relevant_file1.py`
- `path/to/relevant_file2.py`

## Numbered Steps
1. [First discrete implementation step]
2. [Second discrete implementation step]
3. [Third discrete implementation step]

## Allowed Paths and Restrictions

### Allowed Paths
[List strictly which files or directories may be created or edited.]
- `path/to/target_file.py`

### Restrictions
- **NO Terminal Commands**: Do NOT execute any terminal commands, shell scripts, or background processes. Codex performs all verification and test execution.
- **NO Nested Agents**: Do NOT invoke subagents, secondary agents, or background workers.
- **NO Commits / Git Mutations**: Do NOT perform `git commit`, `git push`, `git reset`, or `git checkout`.
- **NO Telegram / 3D/CAD**: Do NOT touch or inspect `scripts/telegram*`, Telegram-related files, or any 3D/CAD files.
- **Immutable Tests & Schemas**: `tests/` and `schemas/` are strictly immutable; do NOT modify them unless explicit user/owner permission is documented in this task.
- **No Direct API / Secret Access**: Never call external APIs directly or read/access secrets, credentials, or tokens.

## Acceptance Tests Run by Codex
[Specify the exact test command(s) that Codex will run after Gemini completes.]
- `python -m unittest tests.test_<name>`
- `python -m unittest discover tests`

## Final Report
Gemini must provide a final summary report of at most 15 lines containing:
- Changed files
- Completed behavior
- Tests not run (deferred to Codex)
- Remaining issues / notes
