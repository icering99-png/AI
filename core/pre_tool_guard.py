"""core/pre_tool_guard.py — Lifecycle PreToolUse hook enforcing Gate 1 RO lock."""

import json
from pathlib import Path
import re
import sys
import warnings

warnings.simplefilter("ignore")

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.defense_guard import DefenseGuard


def _get_plan(plan_path: Path) -> tuple[str, list[Path]]:
    """Extract status and canonical allowed paths from plan text."""
    if not plan_path.is_file():
        return "MISSING", []
    try:
        txt = plan_path.read_text(encoding="utf-8")
    except OSError:
        return "READ_ERROR", []

    st_m = re.search(r"(?im)^\*\s+\*\*Status:\*\*\s*`?([A-Za-z0-9_]+)`?", txt)
    status = st_m.group(1).strip() if st_m else "UNKNOWN"

    paths: list[Path] = []
    p_m = re.search(r"(?im)^\*\s+\*\*Allowed Paths:\*\*\s*([^\n\r]+)", txt)
    if p_m:
        for p in p_m.group(1).split(","):
            raw = p.strip().strip("`").replace("\\", "/")
            if raw and raw != "*":
                try:
                    paths.append((_ROOT / raw).resolve())
                except (ValueError, OSError):
                    pass
    return status, paths


def _chk_path(target_str: str, allowed: list[Path]) -> bool:
    """Validate target path matches allowed paths strictly without substring bypass."""
    try:
        target = Path(target_str).resolve()
    except (ValueError, OSError):
        return False
    return any(target == ap or target.is_relative_to(ap) for ap in allowed)


def eval_tool(payload: dict) -> dict[str, str]:
    """Evaluate tool call against Gate 1 protection rules."""
    tc = payload.get("toolCall", {})
    name = tc.get("name", "")
    args = tc.get("args", {})

    if name == "run_command":
        cmd = args.get("CommandLine", "")
        ok, reason = DefenseGuard.chk_cmd(cmd)
        if not ok:
            return {"decision": "deny", "reason": f"CMD_VIOLATION: {reason}"}
        return {"decision": "allow"}

    if name not in ("edit_file", "write_file"):
        return {"decision": "allow"}

    path_str = args.get("Path", "")
    if not path_str:
        return {"decision": "deny", "reason": "MISSING_PATH"}

    plan_p = _ROOT / "plans" / "PLAN-LIVE.md"
    try:
        if Path(path_str).resolve() == plan_p.resolve():
            return {"decision": "allow"}
    except Exception:
        pass
    status, allowed = _get_plan(plan_p)

    if status not in ("IN_PROGRESS", "APPROVED"):
        return {"decision": "deny", "reason": f"RO_LOCK: Plan status {status}"}

    if not _chk_path(path_str, allowed):
        return {"decision": "deny", "reason": f"RO_LOCK: {path_str} not in allowed"}

    return {"decision": "allow"}


def main() -> None:
    """Read stdin payload from Antigravity, evaluate and output JSON."""
    try:
        if hasattr(sys.stdin, "reconfigure"):
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")
        raw = sys.stdin.read().strip()
        if not raw:
            res = {"decision": "deny", "reason": "EMPTY_STDIN"}
        else:
            payload = json.loads(raw)
            res = eval_tool(payload)
    except Exception as err:
        res = {"decision": "deny", "reason": f"HOOK_ERROR: {err}"}
    sys.stdout.write(json.dumps(res))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
