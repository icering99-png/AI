"""Golden invariant test suite protecting core functionality from regression."""

import unittest
from core.defense_guard import DefenseGuard
from core.rules_critic import RulesCritic
from core.escalation_router import EscalateRouter


class TestGoldenInvariants(unittest.TestCase):
    """Invariant tests that must never fail."""

    def test_golden_ident_limit(self):
        self.assertFalse(DefenseGuard.chk_ident("def func_name_too_long(): pass")[0])
        self.assertTrue(DefenseGuard.chk_ident("def short_fn(): pass")[0])

    def test_golden_danger_guard(self):
        self.assertFalse(DefenseGuard.chk_danger("eval('1')")[0])

    def test_golden_critic_schema(self):
        v = RulesCritic.audit("eval('1')")
        self.assertEqual(v["verdict"], "REJECT")
        self.assertIn("rule_id", v)

    def test_golden_payload_size(self):
        ok, p = EscalateRouter.pack_payload("g", "c", "e", "w")
        self.assertTrue(ok)
        self.assertLessEqual(len(p), 300)


if __name__ == "__main__":
    unittest.main()
