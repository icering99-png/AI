"""Unit tests verifying AuditLogger integrity and tamper detection."""

import json
import tempfile
import unittest
from pathlib import Path
from core.audit_logger import AuditLogger


class TestAuditLoggerIntegrity(unittest.TestCase):
    """Verifies that AuditLogger produces valid entries and detects tampering."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = Path(self.temp_dir.name) / "test_audit.jsonl"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_01_valid_automated_log_entry(self):
        """AuditLogger generates compliant entry with auto timestamp and hash."""
        logger = AuditLogger(str(self.log_path))
        rec = logger.log(
            step="SUB-TEST",
            target="core/dummy.py",
            status="PASS",
            details={"defense_guard": "PASS"},
        )
        self.assertIn("timestamp", rec)
        self.assertIn("step", rec)
        self.assertIn("entry_hash", rec)
        self.assertTrue(self.log_path.exists())

        # Verify entry on disk
        lines = self.log_path.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 1)
        parsed = json.loads(lines[0])
        self.assertEqual(parsed["step"], "SUB-TEST")
        self.assertEqual(parsed["status"], "PASS")

    def test_02_detect_tampering_or_manual_bypass(self):
        """AuditLogger.verify_log flags manual entries or modified records."""
        logger = AuditLogger(str(self.log_path))
        logger.log(step="SUB-01", target="core/a.py", status="PASS")

        # Manually inject entry without valid hash/schema
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"manual": "bypass", "status": "FAKE"}) + "\n")

        valid, err = logger.verify_log()
        self.assertFalse(valid)
        self.assertIn("TAMPERED_OR_INVALID_SCHEMA", err)


if __name__ == "__main__":
    unittest.main()
