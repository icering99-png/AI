"""Deterministic File Integrity Monitoring (FIM) and Sandbox Guard."""
from __future__ import annotations
import hashlib
from pathlib import Path


class IntegrityGuard:
    """Enforces absolute path jail and file hash integrity checks."""

    @staticmethod
    def chk_jail(target: str, root: str = ".") -> tuple[bool, str]:
        """Verify target path is strictly jailed within repository root."""
        try:
            r = Path(root).resolve()
            t = Path(target).resolve()
            if not t.is_relative_to(r):
                return False, f"JAIL_ESCAPE: '{target}' resolves outside root '{root}'"
            return True, "OK"
        except (ValueError, RuntimeError) as err:
            return False, f"JAIL_ERROR: {err}"

    @staticmethod
    def snapshot(paths: list[str]) -> dict[str, str]:
        """Compute SHA-256 snapshot for a list of existing files."""
        hashes: dict[str, str] = {}
        for p_str in paths:
            p = Path(p_str).resolve()
            if p.is_file():
                h = hashlib.sha256(p.read_bytes()).hexdigest()
                hashes[str(p)] = h
        return hashes

    @staticmethod
    def verify(baseline: dict[str, str]) -> tuple[bool, list[str]]:
        """Verify files match baseline hashes; return list of drifted files."""
        drifted: list[str] = []
        for p_str, expected in baseline.items():
            p = Path(p_str)
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != expected:
                drifted.append(p_str)
        return len(drifted) == 0, drifted
