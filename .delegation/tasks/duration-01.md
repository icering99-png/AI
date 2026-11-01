# Goal
Implement a small duration parser and tests as the end-to-end delegation exercise.

# Context
Owner approved this exercise in plans/PLAN-LIVE.md. Follow AGENTS.md; use file tools only. Codex is your orchestrator and will execute tests.

# Steps
1. Create sandbox/duration.py with parse_duration(value: str) -> int. Parse duration tokens with non-negative integer counts and h, m, s units, separated by spaces. Example: 1h 30m 15s returns 5415. Allow a single token and zero-valued counts. Raise TypeError for non-string input and ValueError for malformed syntax, negative counts, unsupported units, or trailing garbage.
2. Create sandbox/test_duration.py using unittest, covering examples, zero values, supported units and the specified failures. Use an import compatible with `python -m unittest discover -s sandbox -p test_duration.py`.
3. Do not run any terminal commands or commit. Return at most 15 lines listing changed files and what Codex should verify.

# Allowed Paths
Only sandbox/duration.py and sandbox/test_duration.py. No Telegram, 3D/CAD, core/, tests/, schemas/, settings, or other files. Do not spawn agents, install dependencies, read secrets, or change the approved plan.

# Acceptance
Codex runs `python -m unittest discover -s sandbox -p test_duration.py` and the unchanged project oracle `python -m unittest discover tests`. Both must exit 0. Implementation and tests must be written by Gemini, with its log retained.
