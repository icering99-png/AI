# core/turn_guard.py
"""Deterministic Turn Guard validating git status against active plan step."""
from __future__ import annotations
from pathlib import Path
import re


class TurnGuard:
    """Validates staged/modified files against active plan step."""

    @staticmethod
    def get_active(plan_txt: str) -> str:
        """Extract target file path of active step from plan text safely."""
        if not isinstance(plan_txt, str) or not plan_txt.strip():
            return ""
        # AUD-FITE-024, AUD-FITE-032, AUD-FITE-033: Case-insensitive active step search and level-2 header scoping
        active_sec = plan_txt
        m_head = re.search(r"(?im)^##\s+active\s+step\b.*$", plan_txt)
        if m_head:
            rest = plan_txt[m_head.end():]
            m_next = re.search(r"(?m)^##\s+", rest)
            active_sec = rest[:m_next.start()] if m_next else rest
        match = re.search(
            r"\*\s*\*\*(?:Target File|Allowed Paths):\*\*\s*`?([^`\r\n]+)`?",
            active_sec,
        )
        if match:
            return Path(match.group(1).strip()).as_posix().lower()
        return ""

    @classmethod
    def chk_diff(cls, diff_files: list[str], plan_txt: str) -> tuple[bool, str]:
        """Verify changed files match active step target file strictly."""
        if not isinstance(diff_files, (list, tuple)):
            return False, "BLOCKED: Invalid diff_files type."
        if not isinstance(plan_txt, str):
            return False, "BLOCKED: Invalid plan_txt type."
        active = cls.get_active(plan_txt)
        if not active:
            return False, "BLOCKED: No active step found in plan."

        norm_active = Path(active).as_posix().lower()

        clean: list[str] = []
        for f in diff_files:
            if isinstance(f, str) and f.strip():
                clean.append(Path(f.strip()).as_posix().lower())

        # AUD-FITE-016: Strict exact equality without dangerous endswith substring matching
        targets = [p for p in clean if p != "plans/plan-live.md"]
        if not targets:
            return False, "BLOCKED: No changes detected to target file."

        unique_targets = list(dict.fromkeys(targets))
        if len(unique_targets) > 1:
            return False, f"BLOCKED: Turn budget exceeded ({len(unique_targets)} files > 1 file per turn)."

        if unique_targets[0] != norm_active:
            return False, f"BLOCKED: Modified file '{unique_targets[0]}' does not match active '{norm_active}'."

        return True, f"OK: Active step '{norm_active}' strictly matched."
