# AGENTS.md

## Project
Deterministic guard framework for autonomous AI agents: a pre-tool hook, command and path checks, and a test oracle. Python 3.11, dependencies in requirements.txt. The Telegram gateway in scripts/ and any 3D/CAD material are separate projects: do not touch them.

## Layout
- core/: guard modules. pre_tool_guard.py and defense_guard.py are the live hook.
- tests/: the oracle, owned by the human. Change only on explicit request.
- scratch/: throwaway scripts and reproduction tests. Delete the files here when the fix is done.
- plans/PLAN-LIVE.md: plan of the current task. The hook reads its Status and Allowed Paths.
- HANDOFF.md: bridge between sessions, at most 25 lines. History lives in git log.
- _trash/: files moved out instead of deleted.
- schemas/, failure_index.json, state_manifest.json: data contracts.

## Run and verify
- All tests: python -m unittest discover tests
- One module: python -m unittest tests.test_<name>
Work is done only when the tests pass (exit code 0). Show raw output. Do not swallow errors.

## How we work
1. Write a short plan (3-7 items) in plans/PLAN-LIVE.md and wait for my "ok" before editing code.
2. One task at a time. If you notice an unrelated bug, list it at the end of your reply and do not fix it.
3. Change code only where the task needs it. No drive-by refactoring.
4. Reproduce a bug first with a failing test in scratch/, then write the minimal fix in core/. Move the test into tests/ only with my confirmation.
5. If the task is unclear, ask. Do not guess.
6. Keep it simple: no code for hypothetical failures.

## Never do (and why)
- Do not delete files or folders (rm, del, Remove-Item, git rm, git clean). A deleted file is lost silently. Move it with `git mv <path> _trash/` and tell me the path, the reason and what references it. I decide about permanent deletion. Exception: throwaway files inside scratch/.
- Do not edit tests/, schemas/, .agents/hooks.json or this file unless I ask. They are my check of your work.
- Do not run git push, git reset --hard or git checkout -f. I do these after review.
- Do not hardcode machine paths (G:\..., C:\Users\...).
- Do not swallow exceptions (no bare except or pass) and do not invent values when a tool is unavailable. Say so.
- No network calls unless the task allows them.

## Style
Clear names, small functions, early return, type hints, explicit None handling. One commit = one intent; the message says what and why. Repository files are in English. Talk to me in Russian.

## Definition of done
1. Only files from Allowed Paths changed.
2. python -m unittest discover tests: exit code 0.
3. Changed lines re-read.
4. Report: what changed (2-5 lines), files, test output, open questions. Update HANDOFF.md (max 25 lines).
