#!/usr/bin/env python3
"""
Minimal delegation wrapper for Codex orchestrator -> Gemini implementation agent.
Invokes Antigravity CLI (agy) via stream protocol with accept-edits.
"""

import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import List, Tuple


def resolve_agy() -> str:
    """Resolve agy via shutil.which or %LOCALAPPDATA%/agy/bin/agy.exe."""
    which_path = shutil.which("agy")
    if which_path:
        return which_path
    which_exe = shutil.which("agy.exe")
    if which_exe:
        return which_exe

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidate = Path(local_app_data) / "agy" / "bin" / "agy.exe"
        if candidate.is_file():
            return str(candidate)

    raise FileNotFoundError(
        "Could not resolve 'agy' executable. Ensure 'agy' is on PATH or at %LOCALAPPDATA%/agy/bin/agy.exe"
    )


def resolve_task_path(task_input: str, repo_root: Path) -> Path:
    """Resolve task file strictly within .delegation/tasks/ with .md suffix."""
    tasks_dir = (repo_root / ".delegation" / "tasks").resolve()

    raw_path = Path(task_input)

    # 1. Shorthand: simple name / ID without directory separators
    if len(raw_path.parts) == 1:
        task_name = task_input if task_input.endswith(".md") else f"{task_input}.md"
        candidate = (tasks_dir / task_name).resolve()
        if not candidate.is_relative_to(tasks_dir):
            raise ValueError(f"Task path must resolve within {tasks_dir}, got: {candidate}")
        if not candidate.is_file():
            raise FileNotFoundError(f"Task file not found: {candidate}")
        return candidate

    # 2. Explicit path (relative or absolute)
    if not task_input.endswith(".md"):
        raise ValueError(f"Task file must have .md suffix, got: {task_input}")

    if raw_path.is_absolute():
        resolved = raw_path.resolve()
    else:
        resolved = (repo_root / raw_path).resolve()

    if not resolved.is_relative_to(tasks_dir):
        raise ValueError(f"Task path must resolve within {tasks_dir}, got: {resolved}")

    if not resolved.is_file():
        raise FileNotFoundError(f"Task file not found: {resolved}")

    return resolved


def build_prompt(task_content: str) -> str:
    """Construct execution prompt with mandatory operational constraints."""
    return (
        "You are the Gemini implementation agent working under Codex orchestration.\n\n"
        "CRITICAL OPERATIONAL RULES:\n"
        "1. You may use file read and file edit tools to implement the task.\n"
        "2. DO NOT run terminal commands or shell execution tools under any circumstances. Codex runs all tests and verification.\n"
        "3. DO NOT spawn subagents or background secondary agents.\n"
        "4. Never call external APIs directly or access secrets/tokens.\n"
        "5. Strictly respect Allowed Paths and restrictions in the task specification.\n"
        "6. Provide a concise final report of at most 15 lines.\n\n"
        "TASK SPECIFICATION:\n"
        "===================\n"
        f"{task_content}\n"
    )


def terminate_process_tree(proc: subprocess.Popen) -> None:
    """Terminate the process and any children without leaving orphaned processes."""
    if proc.poll() is not None:
        return

    if sys.platform == "win32":
        try:
            res = subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            if res.returncode != 0 and proc.poll() is None:
                sys.stderr.write(
                    f"Warning: taskkill returned {res.returncode}: {res.stderr.strip()}\n"
                )
        except OSError as err:
            sys.stderr.write(f"Warning: taskkill invocation failed: {err}\n")
    else:
        try:
            pgid = os.getpgid(proc.pid)
            os.killpg(pgid, 15)  # SIGTERM
        except ProcessLookupError:
            return
        except OSError as err:
            sys.stderr.write(f"Warning: SIGTERM process group failed: {err}\n")

    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if sys.platform != "win32":
            try:
                pgid = os.getpgid(proc.pid)
                os.killpg(pgid, 9)  # SIGKILL
            except (ProcessLookupError, OSError):
                sys.stderr.write("Warning: could not signal timed-out process group.\n")
        try:
            proc.kill()
            proc.wait(timeout=5)
        except (subprocess.TimeoutExpired, OSError) as err:
            sys.stderr.write(f"Warning: final kill failed or child still running: {err}\n")


def parse_ndjson_log(log_file: Path) -> Tuple[str | None, str | None]:
    """Extract final result.response text and status from NDJSON lines in log file."""
    last_response: str | None = None
    last_status: str | None = None

    if not log_file.is_file():
        return None, None

    try:
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("=== RUN SEPARATOR:"):
                    last_response, last_status = None, None
                line_str = line.strip()
                if not line_str.startswith("{") or not line_str.endswith("}"):
                    continue
                try:
                    payload = json.loads(line_str)
                except json.JSONDecodeError:
                    continue

                if not isinstance(payload, dict):
                    continue

                # Documented response forms: {"event": "result", "status": "...", "response": "..."}
                # or {"result": {"status": "...", "response": "..."}}
                status = payload.get("status")
                response = payload.get("response")

                if "result" in payload and isinstance(payload["result"], dict):
                    status = payload["result"].get("status", status)
                    response = payload["result"].get("response", response)

                if status is not None:
                    last_status = str(status)
                if response is not None:
                    last_response = str(response)
    except OSError as err:
        sys.stderr.write(f"Warning: could not read log for NDJSON parsing: {err}\n")

    return last_response, last_status


def read_log_tail(log_file: Path, max_lines: int = 30) -> List[str]:
    """Read the last max_lines lines from the log file."""
    if not log_file.is_file():
        return []
    try:
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
            return [line.rstrip("\r\n") for line in lines[-max_lines:]]
    except OSError as err:
        sys.stderr.write(f"Warning: could not read log tail: {err}\n")
        return []


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Delegate implementation task to Gemini via Antigravity CLI (agy)."
    )
    parser.add_argument(
        "task",
        metavar="TASK",
        help="Task ID or filename (.md inside .delegation/tasks/)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=900,
        help="Timeout in seconds (default: 900)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-3.8-flash-low",
        help="Model name (must start with 'gemini-'; default: gemini-3.8-flash-low)",
    )

    args = parser.parse_args(argv)

    if args.timeout <= 0:
        sys.stderr.write(f"Error: --timeout must be positive, got {args.timeout}\n")
        return 1

    if not args.model.startswith("gemini-"):
        sys.stderr.write(f"Error: --model must start with 'gemini-', got '{args.model}'\n")
        return 1

    repo_root = Path(__file__).resolve().parent.parent

    try:
        agy_bin = resolve_agy()
        task_file = resolve_task_path(args.task, repo_root)
    except Exception as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1

    # Warn once about permissions and host environment
    sys.stderr.write(
        "Warning: --mode accept-edits approves file edits automatically, "
        "but terminal command permissions remain and no OS sandbox is provided.\n"
    )

    logs_dir = repo_root / ".delegation" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / f"{task_file.stem}.log"

    task_content = task_file.read_text(encoding="utf-8")
    long_prompt = build_prompt(task_content)

    input_event = json.dumps(
        {"event": "user", "message": {"content": long_prompt}},
        ensure_ascii=False,
    ) + "\n"

    cmd = [
        agy_bin,
        "--input-format",
        "stream-json",
        "--output-format",
        "stream-json",
        "--mode",
        "accept-edits",
        "--model",
        args.model,
    ]

    timed_out = False
    exit_code = 1
    launch_error: str | None = None

    # Write run separator if log exists
    if log_file.exists():
        sep = (
            f"\n{'=' * 60}\n"
            f"=== RUN SEPARATOR: {datetime.datetime.now(datetime.timezone.utc).isoformat()} ===\n"
            f"{'=' * 60}\n"
        )
        try:
            with open(log_file, "a", encoding="utf-8", errors="replace") as f:
                f.write(sep)
        except OSError as err:
            sys.stderr.write(f"Warning: could not write run separator: {err}\n")

    try:
        with open(log_file, "a", encoding="utf-8", errors="replace") as log_out:
            popen_kwargs = {
                "stdin": subprocess.PIPE,
                "stdout": log_out,
                "stderr": subprocess.STDOUT,
                "cwd": str(repo_root),
                "shell": False,
            }
            if sys.platform != "win32":
                popen_kwargs["start_new_session"] = True

            try:
                proc = subprocess.Popen(cmd, **popen_kwargs)
            except OSError as exc:
                launch_error = f"[LAUNCH ERROR] Failed to start agy process: {exc}\n"
                log_out.write(launch_error)
                log_out.flush()
                sys.stderr.write(launch_error)
                print(f"Return code: 1")
                print(f"Log path: {log_file}")
                print(launch_error.strip())
                return 1

            try:
                proc.communicate(
                    input=input_event.encode("utf-8"),
                    timeout=args.timeout,
                )
                exit_code = proc.returncode
            except subprocess.TimeoutExpired:
                timed_out = True
                exit_code = 124
                terminate_process_tree(proc)
                timeout_msg = (
                    f"\n[DELEGATION TIMEOUT] Subprocess timed out after {args.timeout}s (exit 124).\n"
                )
                log_out.write(timeout_msg)
                log_out.flush()
    except OSError as err:
        sys.stderr.write(f"Execution/IO error: {err}\n")
        return 1

    final_response, final_status = parse_ndjson_log(log_file)

    if not timed_out and exit_code == 0:
        if final_status != "SUCCESS":
            exit_code = 1
            failure_note = f"\n[DELEGATION FAILURE] Non-success status reported: {final_status}\n"
            try:
                with open(log_file, "a", encoding="utf-8", errors="replace") as f:
                    f.write(failure_note)
            except OSError:
                sys.stderr.write("Error: could not append failure status to log.\n")
    elif not timed_out and exit_code != 0:
        failure_note = f"\n[DELEGATION FAILURE] Subprocess exited with code {exit_code}.\n"
        try:
            with open(log_file, "a", encoding="utf-8", errors="replace") as f:
                f.write(failure_note)
        except OSError:
            sys.stderr.write("Error: could not append process failure to log.\n")

    print(f"Return code: {exit_code}")
    print(f"Log path: {log_file}")

    if final_response:
        summary_lines = final_response.strip().splitlines()
        tail = summary_lines[-30:] if len(summary_lines) > 30 else summary_lines
        for line in tail:
            print(line)
    else:
        tail_lines = read_log_tail(log_file, max_lines=30)
        for line in tail_lines:
            print(line)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
