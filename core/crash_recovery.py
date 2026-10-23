"""core/crash_recovery.py — Write-Ahead checkpoint and safe recovery module."""

import hashlib
import json
import os
from pathlib import Path
import re

_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")


def _chk_target(path_str: str, root_str: str) -> tuple[bool, Path | None, str]:
    """Validate path sandbox and existence."""
    if not isinstance(path_str, str) or not path_str.strip():
        return False, None, "INVALID_PATH"
    try:
        root_p = Path(root_str).resolve()
        target_p = Path(path_str).resolve()
    except (ValueError, OSError, RuntimeError) as err:
        return False, None, f"PATH_ERROR: {err}"
    if not target_p.is_relative_to(root_p):
        return False, None, f"ESCAPE_VIOLATION: {path_str}"
    return True, target_p, "OK"


def _calc_hash(target_p: Path) -> tuple[bool, str, str]:
    """Calculate chunked SHA-256 for a file safely."""
    hasher = hashlib.sha256()
    try:
        with open(target_p, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return True, hasher.hexdigest(), "OK"
    except (PermissionError, OSError) as err:
        return False, "", f"READ_ERROR: {err}"


def safe_read(path_str: str, root_str: str = ".") -> tuple[bool, str, str]:
    """Read file safely in chunks with sandbox check and Windows sharing error handling."""
    ok, target_p, msg = _chk_target(path_str, root_str)
    if not ok or target_p is None:
        return False, "", msg
    if not target_p.is_file():
        return False, "", "FILE_NOT_FOUND"
    return _calc_hash(target_p)


def _fmt_hashes(verified_files: list[str], root_str: str) -> str:
    """Collect safe SHA-256 hashes formatted without YAML injection."""
    hashes: list[str] = []
    for f in verified_files:
        ok, h, _ = safe_read(f, root_str=root_str)
        if ok:
            escaped_path = json.dumps(f)
            hashes.append(f'    - path: {escaped_path}\n      sha256: "{h}"')
    return "\n".join(hashes) if hashes else "    []"


def render_cp(
    run_id: str,
    active_step: str,
    verified_files: list[str],
    root_str: str = ".",
) -> str:
    """Render machine-readable recovery checkpoint preventing YAML injection."""
    if not _SAFE_ID_RE.fullmatch(run_id or ""):
        raise ValueError("Invalid run_id format")
    if not _SAFE_ID_RE.fullmatch(active_step or ""):
        raise ValueError("Invalid active_step format")
    if not isinstance(verified_files, list):
        raise ValueError("verified_files must be a list")

    hashes_block = _fmt_hashes(verified_files, root_str)
    return (
        "```yaml\ncheckpoint_version: \"1.0\"\n"
        f"run_id: {json.dumps(run_id)}\nactive_step: {json.dumps(active_step)}\n"
        f"verified_artifacts:\n{hashes_block}\n```"
    )


def _write_tmp(tmp_p: Path, content: str) -> None:
    """Write content to temporary file with flush and fsync."""
    tmp_p.parent.mkdir(parents=True, exist_ok=True)
    with open(tmp_p, "w", encoding="utf-8") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())


def write_cp(
    target_path: str, content: str, root_str: str = "."
) -> tuple[bool, str]:
    """Atomically write checkpoint to file via .tmp file with fsync."""
    ok, dest_p, msg = _chk_target(target_path, root_str)
    if not ok or dest_p is None:
        return False, msg

    tmp_p = dest_p.with_suffix(".tmp")
    try:
        _write_tmp(tmp_p, content)
        os.replace(tmp_p, dest_p)
        return True, "WRITTEN_ATOMICALLY"
    except (OSError, PermissionError) as err:
        if tmp_p.exists():
            try:
                tmp_p.unlink()
            except OSError:
                pass
        return False, f"WRITE_ERROR: {err}"
