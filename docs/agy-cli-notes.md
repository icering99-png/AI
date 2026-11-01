# Antigravity CLI verification

Verified on 2026-11-01 on Windows with PowerShell 7.6.5.

- Git: 2.53.0.windows.1; the project is already a Git repository.
- Antigravity CLI: 1.4.11, installed under the standard local-user `agy/bin` directory, but absent from this shell's PATH.
- The execution sandbox denied access to the installed binary; version and help were obtained with approved execution outside that sandbox.
- `--print` (`-p`, `--prompt`) runs one prompt noninteractively and prints its response.
- `--input-format text` is the default. Runtime disproved the attempted bare `--print --input-format text` invocation: --print consumed the next flag as its prompt (exit 2). Use verified NDJSON stdin with `--input-format stream-json --output-format stream-json`, one event/user/message/content object and a trailing newline, then close stdin.
- `--output-format` supports `text`, `json`, and `stream-json`.
- No working-directory flag appears in top-level help. The wrapper launches from repository root; stream init events confirmed the correct cwd.
- `--mode accept-edits` was runtime-verified to allow file edits on this host. Gemini is instructed not to run terminal commands; Codex executes tests. This is not OS isolation. `auto` requires the unavailable native sandbox.
- `--model` selects the session model; `models` lists available models.
- `--print-timeout` limits print execution; its default is zero (unlimited).
- `--dangerously-skip-permissions` exists but is not approved for this setup.
- Authentication and quota error signatures have not been established.
- The restricted shell did not find Claude or Python; outside that sandbox, Claude Code, Python 3.11, and Node.js were found. No installation was performed.
- Authenticated `--print 'Reply with exactly one word: ok' --sandbox --mode plan --print-timeout 45s` returned `ok`, exit code 0. This verifies a response, not working terminal isolation.
- `agy models` successfully listed available models.
- The setup executor invocation with `--sandbox --mode auto` reported: `warning: --mode auto is not available because the terminal sandbox is not available on this host; continuing in the default mode.` The reviewer terminated that invocation and its child processes, exit code 1, rather than continuing with weaker permissions. No implementation was produced.
- Host Windows build is 22631. Official documentation requires Windows 11 24H2 or later with the August 2026 update or later for terminal sandboxing. The installed OS does not meet that requirement.
- Official limitation references: https://antigravity.google/docs/cli/modes and https://antigravity.google/docs/sandbox?tab=cli

Official installation reference: https://antigravity.google/docs/cli/install

Runtime logs show Gemini implementation and a separate correction iteration. However, final result ERROR repeatedly contains `local error: tls: bad record MAC`, including the smoke response `ok`. The wrapper returns 1 despite agy's process exit 0. Setup remains incomplete until a clean SUCCESS result is verified. See docs/SETUP.md for test evidence and limitations.
