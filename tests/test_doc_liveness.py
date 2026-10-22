"""Test suite for automated Markdown link and path liveness."""
import unittest
from core.doc_guard import DocGuard


class TestDocLiveness(unittest.TestCase):
    """Guarantees zero broken documentation or schema references."""

    def test_agents_links(self) -> None:
        """Verify AGENTS.md links are 100% resolvable."""
        ok, broken = DocGuard.audit_doc("AGENTS.md")
        self.assertTrue(ok, f"Broken references found: {broken}")

    def test_coding_standards_links(self) -> None:
        """Verify rules/CODING_STANDARDS.md references are resolvable."""
        ok, broken = DocGuard.audit_doc("rules/CODING_STANDARDS.md")
        self.assertTrue(ok, f"Broken references found: {broken}")

    def test_detects_broken_link(self) -> None:
        """Ensure fake link triggers audit failure."""
        ok, broken = DocGuard.audit_doc("tests/fixtures/non_existent.md")
        self.assertFalse(ok)
