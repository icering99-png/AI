# Goal
Codex is the orchestrator; you are the Gemini implementation agent. Create the minimal delegation wrapper and template. This supersedes setup.md; do not create Claude files.

# Context
Read AGENTS.md and the first 40 lines of plans/PLAN-LIVE.md. Owner approved this setup. Do not read Telegram or 3D/CAD files. You may use file read/edit tools, but DO NOT run terminal commands. Codex will run verification. Do not spawn other agents.

# Implement
1. Create scripts/delegate.py, standard library Python 3.11. CLI: python scripts/delegate.py TASK [--timeout SECONDS] [--model MODEL]. Default 900 seconds, model gemini-3.8-flash-high. Resolve agy via shutil.which or environment LOCALAPPDATA/agy/bin/agy.exe. Task must resolve within .delegation/tasks in repository root, with .md suffix. Run subprocess with cwd repository root and shell=False. Read UTF-8 task and send long prompt on stdin with agy --print --input-format text --mode accept-edits --model MODEL --print-timeout SECONDSs. Help confirms flags but plain stdin is not yet runtime verified. Capture combined output to .delegation/logs/ID.log, append run separator if log exists, print only return code, log path, and last 30 lines. subprocess timeout independently enforced (exit 124); on Windows terminate the process tree using taskkill scoped to child PID. No silent exceptions, no guessed auth/quota classifications. Preserve child exit code, log failure detail. No --dangerously-skip-permissions, no sandbox flag because unsupported on host. Warn once that accept-edits approves edits but terminal command permissions remain and no OS sandbox is provided. Prompts must tell executor not to run terminal commands, Codex runs tests. Never call API directly or access secrets/tokens.
2. Create .delegation/TEMPLATE.md: goal; concrete context paths; numbered steps; allowed paths and restrictions; acceptance tests run by Codex; max 15-line final report. Include no terminal commands, no nested agents, no commits, no Telegram/3D, immutable tests/ and schemas/ unless explicit user permission.
3. Create .delegation/CODEX.md: Codex plans and gets owner ok per AGENTS, writes task, launches wrapper; Gemini implements; Codex reviews stat and scoped diffs, runs tests with raw output, sends correction tasks through wrapper, max 3 iterations, commits accepted subtask only with intended changes. No API keys. Future tasks require precise plan Allowed Paths; wrapper is not a security boundary. Limit log reads to tail. No Claude configuration required.
4. Add .delegation/logs/ to existing .gitignore, preserving content.

# Constraints
Only write scripts/delegate.py, .delegation/TEMPLATE.md, .delegation/CODEX.md, .gitignore. Preserve existing working changes. No installs, no global settings, no core/tests/schema changes, no commands or commits. No hypothetical features.

# Report
At most 15 lines: changed files, completed behavior, tests not run (Codex will run), remaining issues.
