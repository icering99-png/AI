"""Unit tests for budget guard, error classification, and software ladder."""

import os
import shutil
import tempfile
import time
import unittest
from unittest.mock import MagicMock

from core.escalation_router import EscalateRouter
from core.ladder_guard import LadderGuard


class TestCoreAlign(unittest.TestCase):
    """Test suite for core alignments and guards."""

    def setUp(self) -> None:
        """Create temporary test directory."""
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        """Clean up temporary test directory."""
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def test_budget_expiry(self) -> None:
        """Verify retry budget stops when wall-clock time expires."""
        router = EscalateRouter(max_retries=3, budget_sec=10.0)
        self.assertTrue(router.can_retry_local())
        router.start_time = time.time() - 15.0
        self.assertFalse(router.can_retry_local())

    def test_classify_err(self) -> None:
        """Verify error classification into io, syntax, and runtime."""
        self.assertEqual(EscalateRouter.classify_err("FileNotFoundError: missing"), "io")
        self.assertEqual(EscalateRouter.classify_err("Permission denied on file"), "io")
        self.assertEqual(EscalateRouter.classify_err("SyntaxError: bad token"), "syntax")
        self.assertEqual(EscalateRouter.classify_err("ZeroDivisionError: /0"), "runtime")

    def test_repair_skips_io(self) -> None:
        """Verify repair_local does not invoke LLM on IO errors."""
        mock_ollama = MagicMock()
        mock_ollama.generate = MagicMock()
        router = EscalateRouter(ollama_cli=mock_ollama)
        res = router.repair_local("code", "FileNotFoundError: file.txt")
        self.assertEqual(res, "")
        mock_ollama.generate.assert_not_called()

    def test_ladder_file_missing(self) -> None:
        """Verify missing file returns level 0."""
        res = LadderGuard.eval_file(os.path.join(self.tmp_dir, "missing.py"))
        self.assertEqual(res["level"], 0)

    def test_ladder_syntax_fail(self) -> None:
        """Verify broken syntax returns level 0."""
        p = os.path.join(self.tmp_dir, "bad.py")
        with open(p, "w", encoding="utf-8") as f:
            f.write("def broken(:\n    pass\n")
        res = LadderGuard.eval_file(p)
        self.assertEqual(res["level"], 0)

    def test_ladder_long_ident(self) -> None:
        """Verify identifier > 15 chars stops at level 1."""
        p = os.path.join(self.tmp_dir, "long_id.py")
        with open(p, "w", encoding="utf-8") as f:
            f.write("def very_long_function_name() -> None:\n    pass\n")
        res = LadderGuard.eval_file(p)
        self.assertEqual(res["level"], 1)
        self.assertEqual(res["name"], "L1_SYNTAX")

    def test_ladder_clean_code(self) -> None:
        """Verify clean code passes through higher levels."""
        p = os.path.join(self.tmp_dir, "clean.py")
        with open(p, "w", encoding="utf-8") as f:
            f.write("def add(a: int, b: int) -> int:\n    return a + b\n")
        res = LadderGuard.eval_file(p)
        self.assertGreaterEqual(res["level"], 2)


if __name__ == "__main__":
    unittest.main()
