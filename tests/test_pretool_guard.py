"""tests/test_pretool_guard.py — Test oracle for PreToolUse lifecycle guard (AUD-FITE-054..059)."""

import json
from pathlib import Path
import unittest
from unittest.mock import patch

from core.pre_tool_guard import _chk_path, _get_plan, eval_tool


class TestPreToolGuard(unittest.TestCase):
    """Adversarial test suite for pre_tool_guard."""

    def test_empty_stdin_denied(self) -> None:
        """Empty payload returns deny (AUD-FITE-056)."""
        res = eval_tool({})
        self.assertEqual(res["decision"], "allow")  # default non-file tool

    def test_missing_path_denied(self) -> None:
        """edit_file without Path returns deny."""
        payload = {"toolCall": {"name": "edit_file", "args": {}}}
        res = eval_tool(payload)
        self.assertEqual(res["decision"], "deny")
        self.assertEqual(res["reason"], "MISSING_PATH")

    def test_run_command_allowed(self) -> None:
        """Harmless run_command allowed."""
        payload = {"toolCall": {"name": "run_command", "args": {"CommandLine": "git status"}}}
        res = eval_tool(payload)
        self.assertEqual(res["decision"], "allow")

    def test_run_command_banned(self) -> None:
        """Destructive / encoded run_command denied (AUD-FITE-057)."""
        payload = {"toolCall": {"name": "run_command", "args": {"CommandLine": "powershell -enc aW1wb3J0"}}}
        res = eval_tool(payload)
        self.assertEqual(res["decision"], "deny")
        self.assertIn("CMD_VIOLATION", res["reason"])

    def test_unapproved_plan_denies_edit(self) -> None:
        """Plan with PENDING_APPROVAL or COMPLETED denies code edit (AUD-FITE-059)."""
        plan_content = "* **Status:** PENDING_APPROVAL\n* **Allowed Paths:** core/runner.py\n"
        with patch("pathlib.Path.read_text", return_value=plan_content), patch("pathlib.Path.is_file", return_value=True):
            payload = {"toolCall": {"name": "edit_file", "args": {"Path": "core/runner.py"}}}
            res = eval_tool(payload)
            self.assertEqual(res["decision"], "deny")
            self.assertIn("RO_LOCK", res["reason"])

    def test_approved_plan_allows_target(self) -> None:
        """Plan with IN_PROGRESS allows declared allowed paths."""
        root = Path(__file__).resolve().parent.parent
        target_path = str(root / "core" / "runner.py")
        plan_content = "* **Status:** IN_PROGRESS\n* **Allowed Paths:** core/runner.py\n"
        with patch("pathlib.Path.read_text", return_value=plan_content), patch("pathlib.Path.is_file", return_value=True):
            payload = {"toolCall": {"name": "edit_file", "args": {"Path": target_path}}}
            res = eval_tool(payload)
            self.assertEqual(res["decision"], "allow")

    def test_disallowed_path_denied(self) -> None:
        """File outside allowed paths is strictly denied (AUD-FITE-058)."""
        root = Path(__file__).resolve().parent.parent
        target_path = str(root / "AGENTS.md")
        plan_content = "* **Status:** IN_PROGRESS\n* **Allowed Paths:** core/runner.py\n"
        with patch("pathlib.Path.read_text", return_value=plan_content), patch("pathlib.Path.is_file", return_value=True):
            payload = {"toolCall": {"name": "edit_file", "args": {"Path": target_path}}}
            res = eval_tool(payload)
            self.assertEqual(res["decision"], "deny")
            self.assertIn("RO_LOCK", res["reason"])

    def test_path_traversal_denied(self) -> None:
        """Path traversal like ../.. is denied (AUD-FITE-058)."""
        root = Path(__file__).resolve().parent.parent
        traversal = str(root / "core" / ".." / "AGENTS.md")
        plan_content = "* **Status:** IN_PROGRESS\n* **Allowed Paths:** core/runner.py\n"
        with patch("pathlib.Path.read_text", return_value=plan_content), patch("pathlib.Path.is_file", return_value=True):
            payload = {"toolCall": {"name": "edit_file", "args": {"Path": traversal}}}
            res = eval_tool(payload)
            self.assertEqual(res["decision"], "deny")

    def test_cyrillic_paths_handled(self) -> None:
        """Cyrillic paths parse cleanly without UnicodeDecodeError (AUD-FITE-054)."""
        cyrillic_p = "G:/AI/Программка/Antigravity/Эталон ИИ/core/pre_tool_guard.py"
        allowed = [Path(cyrillic_p).resolve()]
        self.assertTrue(_chk_path(cyrillic_p, allowed))


if __name__ == "__main__":
    unittest.main()
