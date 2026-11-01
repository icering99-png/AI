# Goal
Correct the reviewed wrapper before acceptance. Iteration 2 of at most 3 for the setup subtask.

# Context
Read scripts/delegate.py and scratch/test_delegate_paths.py. Only file tools; no terminal commands, nested agents or commits. Codex runs tests. Preserve Telegram/3D/CAD and all unrelated files.

# Corrections
0. Runtime verification failed before contacting Gemini: `--print` without an attached prompt consumed `--input-format` as the prompt (exit 2). Replace plain stdin with the documented stream protocol: arguments --input-format stream-json --output-format stream-json, NO --print flag. Send exactly one newline-terminated JSON object {"event":"user","message":{"content":long_prompt}} on stdin, then close stdin using communicate. These flags and the event/message/content shape were verified from installed help and official https://antigravity.google/docs/cli/headless/. Log full NDJSON and stderr to disk; extract the final result.response for the concise stdout summary, keeping log path and real exit code. If a result reports non-success status despite process exit 0, report it as failure. Do not invent status values; use SUCCESS as documented, report other statuses as non-success. Preserve timeout detection.
1. resolve_task_path currently silently rewrites outside/duration-01.md to the existing tasks/duration-01.md. Reject paths outside .delegation/tasks instead. Accept a direct task ID/basename as documented shorthand, or an explicit path whose resolved location is inside tasks. Enforce the final .md suffix (currently absent for absolute inputs).
2. Remove swallowed exceptions: the timeout handler has `except Exception: pass`, and taskkill discards diagnostics and ignores failure. Catch only expected failures, report them, verify the child exits, and preserve available output. Never silently leave a timed-out process running. On Windows use taskkill child PID tree; on POSIX start a separate process session and terminate that process group.
3. Avoid duplicated captured output after timeout: a second communicate returns all accumulated data, not just additional bytes. Prefer writing combined stdout/stderr directly to the log file opened before process launch, then read its last 30 lines after completion. Stream output to disk so it survives interruption. Log launch failures too. Keep returned child exit codes, timeout code 124, and concise summary even for a logged launch error.
4. Reject timeout <= 0 before spawning. Restrict --model to Gemini slugs (must begin gemini-) because this wrapper promises Gemini execution. Keep no shell=True, no API keys, no permission bypass, and current accept-edits mode.
5. .delegation/CODEX.md: tests/ and schemas/ belong only to the human, not human/Codex. Include git diff --stat before scoped diff, plus review of untracked files. Max 3 implementation iterations total per subtask.

# Allowed Paths
Only scripts/delegate.py and .delegation/CODEX.md. Do not change the reproduction test, core/, tests/, settings, or the plan.

# Acceptance
Codex runs the scratch reproduction (must pass), wrapper --help and validation checks, then executes the duration exercise through the wrapper. Final report at most 15 lines, English repository files.
