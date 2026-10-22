"""Self-verifying oracle checking claim sources consistency with evidence registry."""

import glob
import re
import unittest
from pathlib import Path
import yaml


class TestEvidenceConsistency(unittest.TestCase):
    """Enforces that every SRC-XXXX claim source is registered in the evidence base."""

    def test_all_claim_sources_registered_in_evidence_base(self):
        root = Path(__file__).resolve().parent.parent
        # Locate EVIDENCE_BASE_SOURCES_AND_LINKS.md in parent or parent of parent
        candidates = [
            root.parent / "EVIDENCE_BASE_SOURCES_AND_LINKS.md",
            root.parent.parent / "EVIDENCE_BASE_SOURCES_AND_LINKS.md",
        ]
        parent_evidence = next((c for c in candidates if c.exists()), None)
        self.assertIsNotNone(
            parent_evidence,
            f"Evidence base document not found in candidates: {candidates}",
        )
        evidence_content = parent_evidence.read_text(encoding="utf-8")

        # Scan all claims
        claims_pattern = str(root / "KnowledgeBase" / "claims" / "*.yaml")
        claim_files = glob.glob(claims_pattern)
        self.assertTrue(len(claim_files) >= 16, f"Expected >= 16 claims, found {len(claim_files)}")

        missing = []
        for cf in claim_files:
            with open(cf, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            cid = data.get("id", Path(cf).stem)
            source_info = data.get("source", {})
            src_str = ""
            if isinstance(source_info, dict):
                src_str = source_info.get("id", "") or source_info.get("primary_source", "")
            elif isinstance(source_info, str):
                src_str = source_info

            # Match SRC-XXXX or SRC-XX
            match = re.search(r"SRC-(\d+)", src_str)
            if not match:
                continue

            num = int(match.group(1))
            # Check literal representations: both 4-digit (SRC-0015) and 2-digit (SRC-15)
            src_candidates = [f"SRC-{num:04d}", f"SRC-{num:02d}", f"SRC-{num}"]
            found = any(c in evidence_content for c in src_candidates)
            if not found:
                missing.append((cid, f"SRC-{num:04d}", Path(cf).name))

        self.assertEqual(
            missing,
            [],
            f"Claims reference unregistered sources in EVIDENCE_BASE_SOURCES_AND_LINKS.md: {missing}",
        )


if __name__ == "__main__":
    unittest.main()
