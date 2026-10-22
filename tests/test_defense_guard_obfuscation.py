"""Tests verifying DefenseGuard and RulesCritic detection of dynamic obfuscation."""

import unittest
from core.defense_guard import DefenseGuard
from core.rules_critic import RulesCritic


class TestDefenseGuardObfuscation(unittest.TestCase):
    """Verifies that indirect and obfuscated execution paths are rejected."""

    def test_01_direct_getattr_builtins_eval_rejected(self):
        """getattr(__builtins__, 'ev' + 'al') is caught as dangerous."""
        code = (
            "def exploit():\n"
            "    f = getattr(__builtins__, 'ev' + 'al')\n"
            "    return f('1+1')\n"
        )
        ok, msg = DefenseGuard.chk_danger(code)
        self.assertFalse(ok, "DefenseGuard should reject getattr(__builtins__, ...)")
        self.assertIn("Banned", msg)

    def test_02_vars_builtins_call_rejected(self):
        """vars(__builtins__) indirect lookup is caught."""
        code = (
            "def exploit():\n"
            "    f = vars(__builtins__)['ev' + 'al']\n"
            "    return f('1+1')\n"
        )
        ok, msg = DefenseGuard.chk_danger(code)
        self.assertFalse(ok, "DefenseGuard should reject vars(__builtins__)[...]")
        self.assertIn("Banned", msg)

    def test_03_critic_audits_dynamic_obfuscation(self):
        """RulesCritic.audit rejects dynamic obfuscation without literal eval(."""
        code = (
            "def run_payload():\n"
            "    fn = getattr(__builtins__, 'ex' + 'ec')\n"
            "    fn('import os')\n"
        )
        verdict = RulesCritic.audit(code)
        self.assertEqual(verdict.get("verdict"), "REJECT")
        self.assertEqual(verdict.get("rule_id"), "R001")


if __name__ == "__main__":
    unittest.main()
