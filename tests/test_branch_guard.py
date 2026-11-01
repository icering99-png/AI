"""Unit tests for BranchGuard hypothesis isolation."""
import tempfile
import unittest
from pathlib import Path
from core.branch_guard import BranchGuard


class TestBranchGuard(unittest.TestCase):
    """Test suite for hypothesis branch lifecycle and failure logging."""

    def test_abort_records_failure_index(self) -> None:
        """Verify aborted hypothesis logs to failure index as DISPROVEN."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            fpath = tf.name

        ok = BranchGuard.abort_hypo(
            name="test_bad",
            reason="AST violation",
            fail_path=fpath,
        )
        self.assertTrue(ok)
        import json
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data["failures"]), 1)
        item = data["failures"][0]
        self.assertEqual(item["status"], "DISPROVEN")
        self.assertIn("AST violation", item["root_cause"])

    def test_hypo_branch_name_slugification(self) -> None:
        """Verify hypothesis branch name normalizes dirty names safely."""
        from core.slug_gen import make_slug
        slug = make_slug("Test Dirty Name #123!", max_len=15)
        self.assertEqual(slug, "test-dirty-name")
        self.assertEqual(len(slug), 15)


if __name__ == "__main__":
    unittest.main()
