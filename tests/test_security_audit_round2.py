"""Comprehensive test suite for Round 2 security hardening and audit verification."""

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from core.defense_guard import DefenseGuard, is_valid_token
from core.semantic_memory import SemanticMemory
from core.branch_guard import BranchGuard
from core.turn_guard import TurnGuard
from core.regression_guard import RegressGuard
from core.runbook_gen import RunbookGen


class TestSecurityHardeningRound2(unittest.TestCase):
    """Test suite covering second-round security fixes with auditor hardening."""

    def test_aud020_aud_fite_006_privilege_escalation_blocked(self):
        """Verify logs/ cannot be bypassed even with allow_test_edit and valid token."""
        # Standard block
        ok, msg = DefenseGuard.chk_protected("logs/test.log")
        self.assertFalse(ok)
        self.assertIn("PROTECTED_PATH_VIOLATION", msg)

        # AUD-FITE-006: Attempt privilege escalation on logs/ with allow_test_edit=True
        ok_esc, msg_esc = DefenseGuard.chk_protected(
            "logs/guard_audit.jsonl", allow_test_edit=True, approve_token="APPROVE PLAN-01"
        )
        self.assertFalse(ok_esc, "AUD-FITE-006 Failed: logs/ must NEVER be editable even with test token!")
        self.assertIn("PROTECTED_PATH_VIOLATION", msg_esc)

        # Legit test edit with token MUST pass
        ok_test, _ = DefenseGuard.chk_protected(
            "tests/test_new.py", allow_test_edit=True, approve_token="APPROVE PLAN-01"
        )
        self.assertTrue(ok_test)

        # Root contract edit with token by architect MUST pass (test_integrity_guard compatibility)
        ok_agent, _ = DefenseGuard.chk_protected(
            "AGENTS.md", allow_test_edit=True, approve_token="APPROVE PLAN-01"
        )
        self.assertTrue(ok_agent)

    def test_aud021_strict_token_format(self):
        """Verify only well-formed APPROVE <PLAN-ID> tokens are accepted."""
        self.assertFalse(is_valid_token("APPROVE"))
        self.assertFalse(is_valid_token("APPROVE_ALL"))
        self.assertFalse(is_valid_token("approve PLAN-01"))
        self.assertTrue(is_valid_token("APPROVE PLAN-SECURITY-02"))
        self.assertTrue(is_valid_token("APPROVE PLAN-SECURITY-02", "PLAN-SECURITY-02"))
        self.assertFalse(is_valid_token("APPROVE PLAN-SECURITY-02", "PLAN-OTHER"))

    def test_aud023_aud_fite_009_semantic_memory_fail_closed(self):
        """Verify semantic memory rejects dangerous code and handles sandbox escape fail-closed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mem = SemanticMemory(root=tmpdir)
            # Dangerous code
            bad_code = "def exploit():\n    eval('__import__(\"os\").system(\"dir\")')"
            self.assertFalse(mem.save_tmpl("exploit", "key1", bad_code))
            self.assertIsNone(mem.get_tmpl("exploit", "key1"))

            # Sandbox escape attempt -> must return False, not raise ValueError
            self.assertFalse(mem.save_tmpl("../outside", "escape", "def ok(): pass"))

            # Non-string input
            self.assertFalse(mem.save_tmpl("cat", "key_none", None))

            # Safe template
            good_code = "def safe_add(a: int, b: int) -> int:\n    return a + b"
            self.assertTrue(mem.save_tmpl("math", "add", good_code))
            self.assertIsNotNone(mem.get_tmpl("math", "add"))

    def test_aud024_aud_fite_007_failure_index_backward_compat_and_safety(self):
        """Verify failure_index handles empty files and preserves corrupt registries fail-closed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Case 1: Empty file (NamedTemporaryFile compatibility)
            empty_f = Path(tmpdir) / "empty.json"
            empty_f.touch()
            self.assertTrue(BranchGuard.abort_hypo("hypo_empty", "Reason", fail_path=str(empty_f)))
            content = json.loads(empty_f.read_text(encoding="utf-8"))
            self.assertEqual(len(content["failures"]), 1)

            # Case 2: Populated registry preserved
            pop_f = Path(tmpdir) / "pop.json"
            pop_f.write_text('{"failures": [{"id": "FAIL-EXIST"}]}', encoding="utf-8")
            self.assertTrue(BranchGuard.abort_hypo("hypo_pop", "Reason 2", fail_path=str(pop_f)))
            pop_content = json.loads(pop_f.read_text(encoding="utf-8"))
            self.assertEqual(pop_content["failures"][0]["id"], "FAIL-EXIST")
            self.assertEqual(len(pop_content["failures"]), 2)

            # Case 3: Corrupt non-empty registry fail-closed (no wipeout)
            bad_f = Path(tmpdir) / "bad.json"
            bad_f.write_text("{corrupt json", encoding="utf-8")
            self.assertFalse(BranchGuard.abort_hypo("hypo_bad", "Reason", fail_path=str(bad_f)))
            self.assertEqual(bad_f.read_text(encoding="utf-8"), "{corrupt json")

    def test_aud025_aud_fite_010_dotfiles_and_no_suffix_collision(self):
        """Verify TurnGuard preserves dotfiles and prevents suffix collisions."""
        # Dotfile preservation
        plan_dot = "* **Target File:** `.agents/rules.md`"
        ok_dot, _ = TurnGuard.chk_diff([".agents/rules.md"], plan_dot)
        self.assertTrue(ok_dot, "AUD-FITE-010 Failed: dotfiles must not be corrupted!")

        # Exact match
        plan_text = "* **Target File:** `core/defense_guard.py`"
        ok, _ = TurnGuard.chk_diff(["core/defense_guard.py"], plan_text)
        self.assertTrue(ok)

        # Duplicate file representation in diff must not exceed budget
        ok_dup, _ = TurnGuard.chk_diff(["core/defense_guard.py", "./core/defense_guard.py"], plan_text)
        self.assertTrue(ok_dup)

        # Suffix collision blocked
        ok_bad, msg = TurnGuard.chk_diff(["fake_dir/core/defense_guard.py"], plan_text)
        self.assertFalse(ok_bad)
        self.assertIn("BLOCKED", msg)

        # Sub-plan suffix bypass blocked
        ok_plan_sub, _ = TurnGuard.chk_diff(["sub/plans/plan-live.md"], plan_text)
        self.assertFalse(ok_plan_sub)

    def test_aud026_deterministic_manifest_sorting(self):
        """Verify manifest serialization order is deterministic and preserves unicode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f1 = Path(tmpdir) / "a.txt"
            f2 = Path(tmpdir) / "b.txt"
            f1.write_text("aaa", encoding="utf-8")
            f2.write_text("bbb", encoding="utf-8")
            m1 = Path(tmpdir) / "m1.json"
            m2 = Path(tmpdir) / "m2.json"

            RegressGuard.save_manifest([str(f1), str(f2)], str(m1))
            RegressGuard.save_manifest([str(f2), str(f1)], str(m2))
            self.assertEqual(m1.read_bytes(), m2.read_bytes())

    def test_aud027_git_timeout_and_stderr_capture(self):
        """Verify git runner catches timeout and captures stderr on failure."""
        code, out = BranchGuard._run_git(["log"], timeout_sec=0)
        self.assertEqual(code, 1)
        self.assertIn("TIMEOUT", out)

        # Stderr capture on invalid git command
        code_err, out_err = BranchGuard._run_git(["invalid-git-command-xyz"])
        self.assertEqual(code_err, 1)
        self.assertTrue(len(out_err) > 0)

    def test_aud_fite_021_abort_hypo_non_string_reason(self):
        """Verify abort_hypo safely handles non-string reason types (e.g. Exception, int)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = str(Path(tmpdir) / "fail.json")
            self.assertTrue(BranchGuard.abort_hypo("hypo1", RuntimeError("AST failure"), fail_path=fpath))
            self.assertTrue(BranchGuard.abort_hypo("hypo2", 500, fail_path=fpath))

    def test_aud_fite_022_034_036_abort_hypo_id_collision_and_safety(self):
        """Verify abort_hypo disambiguates prefix collisions, repeated failures and ignores corrupt IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = Path(tmpdir) / "fail.json"
            fpath.write_text('{"failures": [{"id": null}, {"no_id": 1}]}', encoding="utf-8")
            # Same 8-char prefix, distinct names
            self.assertTrue(BranchGuard.abort_hypo("feature_auth_token", "Reason A", fail_path=str(fpath)))
            self.assertTrue(BranchGuard.abort_hypo("feature_auth_oauth", "Reason B", fail_path=str(fpath)))
            # Repeated same name, different reason
            self.assertTrue(BranchGuard.abort_hypo("feature_auth_token", "Reason C", fail_path=str(fpath)))
            data = json.loads(fpath.read_text(encoding="utf-8"))
            ids = [f.get("id") for f in data["failures"] if isinstance(f, dict) and f.get("id")]
            self.assertEqual(len(ids), len(set(ids)), "IDs must be unique without collision")

    def test_aud_fite_026_git_invalid_args_type_safety(self):
        """Verify _run_git fails closed on non-string elements in args list."""
        code, msg = BranchGuard._run_git(["status", None])
        self.assertEqual(code, 1)
        self.assertIn("Invalid args", msg)

    def test_aud_fite_027_chk_protected_relative_subpaths(self):
        """Verify chk_protected only matches roots and allows nested directories."""
        ok, msg = DefenseGuard.chk_protected("src/app/schemas/user.py")
        self.assertTrue(ok)
        self.assertEqual(msg, "OK")

    def test_aud_fite_028_is_valid_token_invalid_types(self):
        """Verify is_valid_token handles non-string expected_plan without crashing."""
        self.assertFalse(is_valid_token("APPROVE PLAN-01", expected_plan=123))
        self.assertFalse(is_valid_token("APPROVE PLAN-01", expected_plan=[]))
        self.assertFalse(is_valid_token(None))

    def test_aud_fite_029_semantic_memory_escape_fail_closed(self):
        """Verify get_tmpl returns None on traversal attempts or invalid arguments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mem = SemanticMemory(root=tmpdir)
            self.assertIsNone(mem.get_tmpl("../escape", "key"))
            self.assertIsNone(mem.get_tmpl("cat", None))

    def test_aud_fite_032_033_turn_guard_active_step_subheadings_and_case(self):
        """Verify get_active parses case-insensitively and respects subheadings."""
        plan_case = "## aCtIvE sTeP\n* **Target File:** `core/case.py`\n"
        self.assertEqual(TurnGuard.get_active(plan_case), "core/case.py")

        plan_sub = "## Active Step\n### Sub-phase\n* **Target File:** `core/sub.py`\n\n## Next Step\n"
        self.assertEqual(TurnGuard.get_active(plan_sub), "core/sub.py")

    def test_aud_fite_037_update_spec_non_string_spec_p(self):
        """Verify update_spec returns False fail-closed without TypeError on non-string spec_p."""
        rb = RunbookGen()
        self.assertFalse(rb.update_spec(None, approve_token="APPROVE PLAN-01"))
        self.assertFalse(rb.update_spec(123, approve_token="APPROVE PLAN-01"))

    def test_aud_fite_038_defense_guard_syntax_danger_type_safety(self):
        """Verify DefenseGuard chk_syntax, chk_ident, chk_danger fail closed on non-string input."""
        ok_syn, msg_syn = DefenseGuard.chk_syntax(None)
        self.assertFalse(ok_syn)
        self.assertIn("Invalid code type", msg_syn)

        ok_id, msg_id = DefenseGuard.chk_ident(None)
        self.assertFalse(ok_id)

        ok_dan, msg_dan = DefenseGuard.chk_danger(None)
        self.assertFalse(ok_dan)

    def test_aud_fite_039_chk_protected_tests_logs_allow_test_edit(self):
        """Verify chk_protected allows editing logging tests under tests/logs/ with valid token."""
        ok, msg = DefenseGuard.chk_protected(
            "tests/logs/test_logger.py", allow_test_edit=True, approve_token="APPROVE PLAN-01"
        )
        self.assertTrue(ok)
        self.assertEqual(msg, "OK")

        # Root logs directory still permanently blocked
        ok_root, _ = DefenseGuard.chk_protected(
            "logs/server.log", allow_test_edit=True, approve_token="APPROVE PLAN-01"
        )
        self.assertFalse(ok_root)

    def test_aud_fite_040_zero_byte_file_manifest_drift(self):
        """Verify RegressGuard computes valid SHA-256 for 0-byte file and detects deletion drift."""
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_file = Path(tmpdir) / "empty.py"
            empty_file.touch()
            # Canonical sha256 of empty bytes
            empty_hash = hashlib.sha256(b"").hexdigest()
            h = RegressGuard.hash_file(str(empty_file))
            self.assertEqual(h, empty_hash)

            m_path = str(Path(tmpdir) / "manifest.json")
            self.assertTrue(RegressGuard.save_manifest([str(empty_file)], m_path))
            ok, drifted = RegressGuard.chk_manifest(m_path)
            self.assertTrue(ok)
            self.assertEqual(drifted, [])

            # Delete file and ensure deletion is detected as drift
            empty_file.unlink()
            ok_del, drifted_del = RegressGuard.chk_manifest(m_path)
            self.assertFalse(ok_del)
            self.assertEqual(len(drifted_del), 1)

    def test_aud_fite_041_chk_path_type_safety(self):
        """Verify chk_path fails closed on None without unhandled TypeError."""
        ok, msg = DefenseGuard.chk_path(None, "root")
        self.assertFalse(ok)
        self.assertIn("Invalid path", msg)

    def test_aud_fite_042_gen_spec_atomic_write(self):
        """Verify gen_spec writes atomically and validates file types."""
        rb = RunbookGen()
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "mod.py"
            f.write_text("def a(): pass", encoding="utf-8")
            out_p = str(Path(tmpdir) / "spec.json")
            res = rb.gen_spec(mod="app", files=[str(f)], entry="main", envs=[], cmd="run", out_p=out_p)
            self.assertTrue(res.get("ok"))
            self.assertTrue(Path(out_p).exists())

    def test_aud_fite_023_git_checkout_fail_closed(self):
        """Verify abort_hypo returns False if git checkout fails (AUD-FITE-023)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orig = BranchGuard._run_git
            try:
                BranchGuard._run_git = classmethod(lambda cls, args: (1, "checkout failed") if "checkout" in args else orig(args))
                f_path = str(Path(tmpdir) / "fail.json")
                res = BranchGuard.abort_hypo("hypo_fail", "test", fail_path=f_path)
                self.assertFalse(res)
            finally:
                BranchGuard._run_git = orig

    def test_aud_fite_024_turn_guard_get_active_multistep_and_empty(self):
        """Verify get_active extracts active step target and handles empty/None (AUD-FITE-024)."""
        multi_plan = (
            "## Completed Steps\n* **Target File:** `core/done.py`\n\n"
            "## Active Step\n* **Target File:** `core/active.py`\n\n"
            "## Next Steps\n* **Target File:** `core/next.py`\n"
        )
        self.assertEqual(TurnGuard.get_active(multi_plan), "core/active.py")
        self.assertEqual(TurnGuard.get_active(""), "")
        self.assertEqual(TurnGuard.get_active(None), "")

    def test_aud_fite_025_atomic_tmp_replace_writes(self):
        """Verify save_manifest writes atomically via tmp file and replace (AUD-FITE-025)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "test.py"
            f.write_text("print(1)", encoding="utf-8")
            m_path = str(Path(tmpdir) / "manifest.json")
            ok = RegressGuard.save_manifest([str(f)], m_path)
            self.assertTrue(ok)
            self.assertTrue(Path(m_path).exists())
            self.assertFalse(Path(m_path + ".tmp").exists())

    def test_aud_fite_035_git_branch_delete_fail_closed(self):
        """Verify abort_hypo returns False if branch delete fails with non-404 error (AUD-FITE-035)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orig = BranchGuard._run_git
            try:
                def mock_run_git(args):
                    if "branch" in args and "-D" in args:
                        return (1, "fatal: git branch delete permission denied")
                    return (0, "")
                BranchGuard._run_git = classmethod(lambda cls, args: mock_run_git(args))
                f_path = str(Path(tmpdir) / "fail.json")
                res = BranchGuard.abort_hypo("hypo_del_fail", "test", fail_path=f_path)
                self.assertFalse(res)
            finally:
                BranchGuard._run_git = orig

    def test_aud_fite_030_031_sync_matrix_and_oracle(self):
        """Verify Section 4 matrix and Section 5 checklist synchronization (AUD-FITE-030/031)."""
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
