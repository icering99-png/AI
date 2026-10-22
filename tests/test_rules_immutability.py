"""Oracle enforcing cryptographic immutability of governance rules and L2 failure index."""
import json
import unittest
from pathlib import Path
from core.artifact_guard import hash_file


class TestRulesImmutability(unittest.TestCase):
    """Enforces that failure_index.json cannot be mutated without authorized spec update."""

    EXPECTED_FAILURE_INDEX_HASH = "5f067375cd6832df535a0f7a8268857be823ed4597c4b591c4844375a0e2af59"

    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parent.parent
        self.fail_idx_path = self.root / "failure_index.json"

    def test_failure_index_integrity_hash(self) -> None:
        """Verify failure_index.json content matches verified baseline hash."""
        self.assertTrue(self.fail_idx_path.exists(), "failure_index.json missing")
        actual_hash = hash_file(str(self.fail_idx_path))
        self.assertEqual(
            actual_hash,
            self.EXPECTED_FAILURE_INDEX_HASH,
            f"MUTATION_DETECTED: failure_index.json was modified without legitimate authorized hash update! Expected {self.EXPECTED_FAILURE_INDEX_HASH}, got {actual_hash}",
        )

    def test_failure_index_has_resolved_failures(self) -> None:
        """Verify core historical failures FAIL-0001 to FAIL-0016 exist in failures list."""
        data = json.loads(self.fail_idx_path.read_text(encoding="utf-8"))
        ids = {item["id"] for item in data.get("failures", [])}
        for expected_id in ("FAIL-0001", "FAIL-0004", "FAIL-0007", "FAIL-0010", "FAIL-0012", "FAIL-0013", "FAIL-0014", "FAIL-0015", "FAIL-0016"):
            self.assertIn(expected_id, ids, f"Historical failure record {expected_id} was removed from failure index")


if __name__ == "__main__":
    unittest.main()
