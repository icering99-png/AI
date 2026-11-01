# Codex and Gemini delegation

## Roles

Codex is the orchestrator: plans, task specifications, review, test execution, and acceptance. Gemini is the implementation agent, accessed through the installed Antigravity CLI and its existing subscription login. No API keys are required by this workflow.

Telegram and 3D/CAD projects are excluded. The repository's AGENTS.md remains authoritative, including plan approval and the immutable test oracle.

## Installation and authentication

Antigravity CLI 1.4.11, Python 3.11, Git, and Node.js were already installed. No software was installed. A restricted Codex shell may not expose the same PATH as the user's normal shell. The wrapper resolves the standard user installation through LOCALAPPDATA when agy is not on PATH.

For initial login or expired authentication, launch `agy` interactively in your own terminal and follow its sign-in prompts. Codex must not retrieve or copy credentials or tokens. Check current options using `agy --help`.

## Project workflow

The project skill is `.agents/skills/delegate-gemini/SKILL.md`; use `$delegate-gemini` in a new Codex chat to request this workflow explicitly. A running chat may need reopening before the skill appears in its skill inventory.

Read `.delegation/CODEX.md`, obtain the required approval of the task plan, then create `.delegation/tasks/<id>.md` from `.delegation/TEMPLATE.md` with exact paths and acceptance criteria.

Run `python scripts/delegate.py .delegation/tasks/<id>.md`. Codex reviews the return code and log tail, inspects the changes, and runs acceptance tests independently. Corrections are separate delegated tasks; stop after three implementation iterations on the same subtask. The default deadline is 900 seconds, configurable with `--timeout`.

## Execution permissions

The verified file-editing mode is `accept-edits`, with the default model pinned to `gemini-3.8-flash-low`, listed by `agy models`. File edits are automatically accepted, while terminal command permissions remain in effect. Tasks prohibit Gemini from running terminal commands; Codex executes tests through its normal tools and approval checks.

Long prompts use UTF-8 NDJSON on stdin: `--input-format stream-json --output-format stream-json`. One user event carries the task; closing stdin ends the session after that turn. The wrapper streams full output to disk, inspects the current run's final result, and requires status `SUCCESS` as well as process exit 0. A missing or unsuccessful result fails even when agy exits 0. Timeout returns 124 and terminates the local process tree. Reused logs cannot reuse a previous run's success.

This is not an OS sandbox or a path-enforcement boundary. Task Allowed Paths and reviewer checks remain necessary. No permission bypass flags or broad global permissions are configured.

Windows build 22631 does not support agy's terminal sandbox. `--mode auto` warned and fell back to default mode; that initial executor was terminated. For actual terminal isolation, official requirements are Windows 11 24H2 or later with the August 2026 update or later: https://antigravity.google/docs/cli/modes

## Failures and logs

Keep delegation logs local. On quota or authentication errors, report the actual error and stop; do not rotate identities, extract tokens, or substitute API keys. Specific error signatures have not been verified on this account, so do not infer them from arbitrary text.

## Verification status (2026-11-01)

- Authenticated trivial prompt: `ok`, exit 0.
- Repository oracle after implementation: 170 tests passed in 3.978 seconds, exit 0.
- Skill frontmatter validation: `Skill is valid!`, exit 0.
- Wrapper regression checks: 2 temporary tests passed (outside task path rejected; previous log success cannot mask a new incomplete run).
- Independent timeout check: child exit 124 as expected; check exit 0.
- Gemini created sandbox/duration.py and sandbox/test_duration.py through the wrapper. Codex reviewed the first version, reproduced a missing repeated-unit check, sent duration-02.md through the wrapper, and independently verified the fix. Two implementation iterations; 7 sandbox tests and the temporary review reproduction passed.
- Logs: .delegation/logs/duration-01.log, duration-02.log, and smoke.log. These are local ignored artifacts; they record Gemini file-writing activity and actual completion statuses.
- Remaining blocker: repeated `local error: tls: bad record MAC` from the Google service connection causes final status ERROR even though responses and edits arrive. Both duration runs and the final smoke request were correctly reported as wrapper failures (exit 1). No clean successful end-to-end run has been certified. Do not suppress the transport error or disable TLS verification. Investigate the CLI/network separately before calling unattended operation ready.
- No authentication or quota error was observed. No credentials, API keys, or network/security settings were changed.
