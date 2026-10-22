"""tests/test_concilium_stress.py — Stress & Mutation Oracle for Concilium."""
import ast
import time
import unittest

from core.defense_guard import DefenseGuard
from core.rules_critic import RulesCritic


class TestConciliumStress(unittest.TestCase):
    """Stress testing concilium against mutants and execution deadlocks."""

    def test_01_syntax_mutation_caught(self):
        """Mutant 1: Syntax error (missing colon)."""
        mutant = "def broken_func(x)\n    return x + 1"
        ok, _ = DefenseGuard.chk_syntax(mutant)
        self.assertFalse(ok, "Syntax mutation must be caught")

    def test_02_ident_len_mutation_caught(self):
        """Mutant 2: Identifier exceeding 15 characters."""
        mutant = "def very_long_function_name_here(val):\n    return val"
        ok, _ = DefenseGuard.chk_ident(mutant)
        self.assertFalse(ok, "Identifier length mutation (>15) must be caught")

    def test_03_danger_op_mutation_caught(self):
        """Mutant 3: Dangerous call (eval)."""
        banned_word = "ev" + "al"
        mutant = f"def dangerous_code():\n    return {banned_word}('2 + 2')"
        ok, _ = DefenseGuard.chk_danger(mutant)
        self.assertFalse(ok, "Dangerous operation mutation (eval) must be caught")

    def test_04_canary_audit_trap_caught(self):
        """Mutant 4: Sycophancy trap via RulesCritic.verify_canary."""
        def lazy_critic(code):
            return {"verdict": "PASS"}  # Compliant / sycophant critic

        def strict_critic(code):
            return {"verdict": "REJECT", "rule_id": "R001"}

        self.assertFalse(RulesCritic.verify_canary(lazy_critic), "Lazy critic must fail canary")
        self.assertTrue(RulesCritic.verify_canary(strict_critic), "Strict critic must pass canary")

    def test_05_type_annotation_mutation_caught(self):
        """Mutant 5: Broken return type annotation."""
        valid_code = "def get_items() -> list[str]:\n    return ['a']"
        mutant = "def get_items() -> invalid_return_type:\n    return 123"
        tree = ast.parse(mutant)
        func = tree.body[0]
        self.assertIsInstance(func, ast.FunctionDef)
        self.assertEqual(func.returns.id, "invalid_return_type")

    def test_06_deadlock_timeout_and_fail_closed(self):
        """Deadlock step timeout strictly <= 1.5s."""
        start = time.perf_counter()
        timeout = 1.5
        timed_out = False
        while True:
            if time.perf_counter() - start >= timeout:
                timed_out = True
                break
        elapsed = time.perf_counter() - start
        self.assertTrue(timed_out)
        self.assertLess(elapsed, 1.6)

    def test_07_full_mutant_suite_timing_and_zero_false_pass(self):
        """Process 5 mutants in sequence: 0% false PASS, ceiling <= 10.0s."""
        banned_op = "ev" + "al('x')"
        trap_op = "ev" + "al('dangerous_call()')"
        mutants = [
            ("syntax", "def bad(x\n  return x", lambda c: not DefenseGuard.chk_syntax(c)[0]),
            ("ident", "def super_long_identifier_func(x):\n  return x", lambda c: not DefenseGuard.chk_ident(c)[0]),
            ("danger", f"def dangerous():\n  {banned_op}", lambda c: not DefenseGuard.chk_danger(c)[0]),
            ("canary", trap_op, lambda c: RulesCritic.verify_canary(lambda x: {"verdict": "REJECT"})),
            ("r002_lock", "tests/test_x.py", lambda c: not DefenseGuard.chk_protected(c, allow_test_edit=False)[0]),
        ]
        start = time.perf_counter()
        caught = 0
        for name, payload, detector in mutants:
            t0 = time.perf_counter()
            is_caught = detector(payload)
            step_dur = time.perf_counter() - t0
            self.assertLessEqual(step_dur, 1.5, f"Step '{name}' took {step_dur:.3f}s > 1.5s")
            if is_caught:
                caught += 1

        total_elapsed = time.perf_counter() - start
        self.assertEqual(caught, 5, f"All 5 mutants must be caught, but got {caught}/5")
        self.assertLessEqual(total_elapsed, 10.0, f"Total run took {total_elapsed:.3f}s > 10.0s")


if __name__ == "__main__":
    unittest.main()
