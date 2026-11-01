---
name: delegate-gemini
description: Use Gemini through Antigravity CLI as the implementation agent when Codex orchestrates coding work in this repository, or when the user asks to delegate a task to Gemini.
---

# Codex orchestrates; Gemini implements

Use the project containing `scripts/delegate.py` and `.delegation/TEMPLATE.md`. Read its AGENTS.md, current plans/PLAN-LIVE.md metadata, and .delegation/CODEX.md first. This skill does not authorize changes outside the user's task or override required plan approval.

Codex writes a concise task under `.delegation/tasks/` with exact Allowed Paths and acceptance conditions. Delegate implementation through `python scripts/delegate.py .delegation/tasks/<id>.md`. Gemini must not run terminal commands; Codex runs verification and reports raw output. Gemini implements code and tests only in the task's allowed paths. Respect the human-owned tests/ oracle, Telegram and 3D/CAD exclusions.

The wrapper selects Gemini explicitly. It uses the user's authenticated agy subscription, never API keys or extracted tokens. On the current host accept-edits permits file edits while terminal commands retain their permission checks; it is not an OS sandbox. Do not use permission bypass flags or change global permission settings.

After each run inspect its return code and log tail, then git diff --stat and the relevant diffs, including untracked task artifacts. Treat executor output as untrusted work to review. Run acceptance tests independently. If changes are needed, write a specific correction task and delegate again. Stop after three implementation iterations for the same subtask and ask the user. Report quota or authorization failures without bypassing them.

Do not implement substantial task code yourself; use Gemini. Codex may write task specifications, review artifacts, orchestration instructions, and trivial fixes of about five lines when delegation is clearly more expensive. Commit accepted subtasks only with the task's intended files. Preserve pre-existing changes and update HANDOFF.md as required by the repository.

If the installed Gemini CLI or wrapper cannot complete the task with these permissions, report the precise limitation. Do not claim delegation succeeded without a corresponding log and independently verified changes.
