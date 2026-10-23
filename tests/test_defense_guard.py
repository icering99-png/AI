"""Tests for Tier 0 DefenseGuard."""

import unittest
from pathlib import Path
from core.defense_guard import DefenseGuard


class TestDefenseGuard(unittest.TestCase):
    """Test suite for DefenseGuard validation."""

    def test_syntax_valid(self):
        code = "def add(a: int, b: int) -> int:\n    return a + b\n"
        ok, msg = DefenseGuard.chk_syntax(code)
        self.assertTrue(ok)
        self.assertEqual(msg, "OK")

    def test_syntax_invalid(self):
        code = "def bad(x:\n    return"
        ok, msg = DefenseGuard.chk_syntax(code)
        self.assertFalse(ok)
        self.assertTrue(msg.startswith("Syntax:"))

    def test_ident_valid(self):
        code = "def calc(num: int) -> int:\n    res = num * 2\n    return res\n"
        ok, msg = DefenseGuard.chk_ident(code, limit=15)
        self.assertTrue(ok)

    def test_ident_invalid(self):
        code = "def very_long_function_name(x: int) -> int:\n    return x\n"
        ok, msg = DefenseGuard.chk_ident(code, limit=15)
        self.assertFalse(ok)
        self.assertIn("very_long_funct", msg)

    def test_path_exists_and_sandbox(self):
        root = Path(__file__).resolve().parent.parent
        existing = root / "core" / "defense_guard.py"
        ok, msg = DefenseGuard.chk_path(str(existing), str(root))
        self.assertTrue(ok)

    def test_path_not_exists(self):
        root = Path(__file__).resolve().parent.parent
        fake = root / "core" / "non_existent_file.py"
        ok, msg = DefenseGuard.chk_path(str(fake), str(root))
        self.assertFalse(ok)
        self.assertIn("Not found", msg)

    def test_path_escape(self):
        root = Path(__file__).resolve().parent.parent / "core"
        outside = root.parent / "HANDOFF.md"
        ok, msg = DefenseGuard.chk_path(str(outside), str(root))
        self.assertFalse(ok)
        self.assertIn("Escape", msg)

    def test_diff_size(self):
        small_diff = "+ line1\n+ line2\n- line3\n"
        ok, _ = DefenseGuard.chk_diff(small_diff, max_l=30)
        self.assertTrue(ok)

        big_diff = "\n".join([f"+ line_{i}" for i in range(35)])
        ok, msg = DefenseGuard.chk_diff(big_diff, max_l=30)
        self.assertFalse(ok)
        self.assertIn("35 > 30", msg)

    def test_danger_ops(self):
        safe_code = "print('hello')"
        ok, _ = DefenseGuard.chk_danger(safe_code)
        self.assertTrue(ok)

        danger_code = "eval('1 + 1')"
        ok, msg = DefenseGuard.chk_danger(danger_code)
        self.assertFalse(ok)
        self.assertIn("eval", msg)


if __name__ == "__main__":
    unittest.main()
