# Goal
Apply the review correction to the duration exercise: reject repeated units. Iteration 2 of at most 3.

# Context
Read sandbox/duration.py, sandbox/test_duration.py, and scratch/test_duration_review.py. The first implementation and its 5 tests passed. Review found that 1h 2h is accepted; this case was intentionally omitted from the first task to verify the correction cycle. The reviewer reproduced it in scratch. Owner approved this exercise and sandbox tests.

# Steps
1. Minimally modify parse_duration to reject repeated units with ValueError, including duplicates separated by other units. Preserve valid existing behavior, type hints, and errors.
2. Add regression tests to sandbox/test_duration.py for 1h 2h, 1m 2s 3m, and a valid combination of distinct units. Do not modify the scratch reproduction or human oracle.
3. Do not run terminal commands, create nested agents, or commit. Codex executes all verification. Report at most 15 lines.

# Allowed Paths
Only sandbox/duration.py and sandbox/test_duration.py. No Telegram, 3D/CAD, core/, tests/, schemas/, settings, or other files. No secrets, APIs, or installs.

# Acceptance
Codex runs scratch/test_duration_review.py, python -m unittest discover -s sandbox -p test_duration.py, and python -m unittest discover tests. All must exit 0. Both implementation iterations must have wrapper logs.
