"""Tactile verification tests for skills, STE-100 and anonymized protocols."""
import unittest
import json
from pathlib import Path
from core.ste_guard import SteGuard


class TestSkillsAndProtocols(unittest.TestCase):
    """Verifies SteGuard limits and local skills manifest presence."""

    def test_ste100_procedural_and_ambiguity_fallback(self) -> None:
        res_ok = SteGuard.check_step("Limit each procedural step to <= 20 words.")
        self.assertTrue(res_ok["ok"])
        self.assertEqual(res_ok["status"], "PASS")

        res_ambig_dots = SteGuard.check_step("Process item and wait...")
        self.assertFalse(res_ambig_dots["ok"])
        self.assertEqual(res_ambig_dots["status"], "REVIEW")

        res_ambig_paren = SteGuard.check_step("Verify token (unclosed bracket")
        self.assertFalse(res_ambig_paren["ok"])
        self.assertEqual(res_ambig_paren["status"], "REVIEW")

    def test_portable_skills_manifest_and_presence(self) -> None:
        root = Path(__file__).resolve().parent.parent
        skills_dir = root / "skills"
        self.assertTrue(skills_dir.exists())

        expected_skills = [
            "asd_ste100_protocol",
            "gauntlet_loop",
            "prompt_refactor_pocock",
        ]
        for skill_name in expected_skills:
            skill_md = skills_dir / skill_name / "SKILL.md"
            self.assertTrue(skill_md.exists(), f"Missing {skill_name}/SKILL.md")

        plug_p = root / "plugin.json"
        self.assertTrue(plug_p.exists())
        plug = json.loads(plug_p.read_text(encoding="utf-8"))
        self.assertEqual(plug["name"], "antigravity-core-standard")
        self.assertEqual(len(plug["skills"]), 3)
        for s in plug["skills"]:
            self.assertTrue(s.startswith("./skills/"))

    def test_failure_index_invariants(self) -> None:
        root = Path(__file__).resolve().parent.parent
        fail_p = root / "failure_index.json"
        self.assertTrue(fail_p.exists())
        data = json.loads(fail_p.read_text(encoding="utf-8"))
        f8 = next(f for f in data["failures"] if f["id"] == "FAIL-0008")
        self.assertEqual(f8["status"], "RESOLVED")
        f9 = next(f for f in data["failures"] if f["id"] == "FAIL-0009")
        self.assertEqual(f9["status"], "RESOLVED")


if __name__ == "__main__":
    unittest.main()
