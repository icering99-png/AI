"""Unit tests for code stripper, think cleaner, and oracle immutability."""

import unittest
from core.defense_guard import DefenseGuard
from core.ollama_client import OllamaClient
from core.rules_critic import RulesCritic


class TestIntegrityGuard(unittest.TestCase):
    """Test suite for code extraction, reasoning stripping, and oracle protection."""

    def test_strip_code_with_fence(self) -> None:
        """Verify markdown fences and preambles are cleanly extracted."""
        raw = "Here is the solution:\n```python\ndef add(a, b):\n    return a + b\n```\nHope it helps!"
        res = OllamaClient.strip_code(raw)
        self.assertEqual(res, "def add(a, b):\n    return a + b")

    def test_strip_code_raw_text(self) -> None:
        """Verify raw text without markdown is preserved cleanly."""
        raw = "def mul(a, b):\n    return a * b"
        res = OllamaClient.strip_code(raw)
        self.assertEqual(res, raw)

    def test_strip_code_fence_no_lang(self) -> None:
        """Verify code blocks without explicit language tag are parsed."""
        raw = "Prefix\n```\nval = 42\n```\nSuffix"
        res = OllamaClient.strip_code(raw)
        self.assertEqual(res, "val = 42")

    def test_protected_roots_blocked_for_worker(self) -> None:
        """Verify tests and schemas cannot be modified by worker."""
        ok_t, _ = DefenseGuard.chk_protected("tests/test_foo.py", allow_test_edit=False)
        self.assertFalse(ok_t)
        ok_s, _ = DefenseGuard.chk_protected("schemas/critic_verdict.json", allow_test_edit=False)
        self.assertFalse(ok_s)
        ok_r, _ = DefenseGuard.chk_protected("rules/CODING_STANDARDS.md", allow_test_edit=False)
        self.assertFalse(ok_r)
        ok_k, _ = DefenseGuard.chk_protected("KnowledgeBase/manifest.yaml", allow_test_edit=False)
        self.assertFalse(ok_k)

    def test_protected_files_blocked_for_worker(self) -> None:
        """Verify root contract files are blocked for worker."""
        ok_a, _ = DefenseGuard.chk_protected("AGENTS.md", allow_test_edit=False)
        self.assertFalse(ok_a)
        ok_f, _ = DefenseGuard.chk_protected("failure_index.json", allow_test_edit=False)
        self.assertFalse(ok_f)

    def test_protected_path_allowed_for_architect(self) -> None:
        """Verify architect with explicit approved plan can edit tests/schemas."""
        # Without token -> must be rejected
        ok_fail, _ = DefenseGuard.chk_protected("tests/test_foo.py", allow_test_edit=True, approve_token="")
        self.assertFalse(ok_fail)
        # With valid token -> allowed
        ok_t, _ = DefenseGuard.chk_protected("tests/test_foo.py", allow_test_edit=True, approve_token="APPROVE SUB-02")
        self.assertTrue(ok_t)
        ok_a, _ = DefenseGuard.chk_protected("AGENTS.md", allow_test_edit=True, approve_token="APPROVE SUB-02")
        self.assertTrue(ok_a)

    def test_unprotected_source_allowed(self) -> None:
        """Verify regular application source files are allowed for worker."""
        ok, _ = DefenseGuard.chk_protected("core/fast_router.py", allow_test_edit=False)
        self.assertTrue(ok)

    def test_critic_r002_backstop_rejection(self) -> None:
        """Verify RulesCritic rejects unauthorized test manipulation via R002."""
        verdict = RulesCritic.audit(
            code="def test_tamper(): pass",
            touch_path="tests/test_core.py",
            allow_test_edit=False,
        )
        self.assertEqual(verdict.get("verdict"), "REJECT")
        self.assertEqual(verdict.get("rule_id"), "R002")

    def test_critic_r002_allowed_for_architect(self) -> None:
        """Verify RulesCritic passes when touch_path is authorized with approve_token."""
        # Without token -> REJECT
        v_fail = RulesCritic.audit(
            code="def add(): pass",
            touch_path="tests/test_core.py",
            allow_test_edit=True,
            approve_token="",
        )
        self.assertEqual(v_fail.get("verdict"), "REJECT")
        # With valid token -> PASS
        verdict = RulesCritic.audit(
            code="def add(): pass",
            touch_path="tests/test_core.py",
            allow_test_edit=True,
            approve_token="APPROVE SUB-02",
        )
        self.assertEqual(verdict.get("verdict"), "PASS")


    def test_integrity_guard_jail_and_drift(self) -> None:
        """Verify absolute path containment and SHA-256 drift detection."""
        import tempfile
        from pathlib import Path
        from core.integrity_guard import IntegrityGuard

        with tempfile.TemporaryDirectory() as td:
            r = Path(td)
            f = r / "test.txt"
            f.write_text("orig", encoding="utf-8")
            ok_jail, _ = IntegrityGuard.chk_jail(str(f), str(r))
            self.assertTrue(ok_jail)
            bad_jail, _ = IntegrityGuard.chk_jail(str(r / "../escape.txt"), str(r))
            self.assertFalse(bad_jail)

            s = IntegrityGuard.snapshot([str(f)])
            v_ok, drift_ok = IntegrityGuard.verify(s)
            self.assertTrue(v_ok)
            self.assertEqual(len(drift_ok), 0)

            f.write_text("tampered", encoding="utf-8")
            v_bad, drift_bad = IntegrityGuard.verify(s)
            self.assertFalse(v_bad)
            self.assertIn(str(f.resolve()), drift_bad)

    def test_doc_guard_frontmatter_audit(self) -> None:
        """Verify DocGuard validates frontmatter YAML structure."""
        import tempfile
        from pathlib import Path
        from core.doc_guard import DocGuard

        with tempfile.TemporaryDirectory() as td:
            r = Path(td)
            good_f = r / "valid.md"
            good_f.write_text("---\nname: valid\napplyTo: '**/*.py'\n---\nBody", encoding="utf-8")
            bad_f = r / "bad.md"
            bad_f.write_text("name: no_delimiters\nBody", encoding="utf-8")

            ok_v, _ = DocGuard.audit_front(str(good_f))
            self.assertTrue(ok_v)
            ok_b, _ = DocGuard.audit_front(str(bad_f))
            self.assertFalse(ok_b)


if __name__ == "__main__":
    unittest.main()
