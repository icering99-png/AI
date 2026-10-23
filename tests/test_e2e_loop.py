"""End-to-end adversarial closed-loop test."""
import unittest
from core.escalation_router import EscalateRouter
from core.runner import PipelineRunner


class MockLLM:
    """Mock LLM repairing broken code."""

    def generate(self, prompt: str) -> str:
        """Return valid fixed code."""
        return "def add(x: int) -> int:\n    return x + 1\n"


class TestE2ELoop(unittest.TestCase):
    """Test full cycle: reject -> local fix -> approve -> escalate."""

    def test_e2e_cycle(self) -> None:
        """Verify full repair loop and packet fallback."""
        runner = PipelineRunner(ollama=MockLLM())
        bad = "def add_number_value_exceed(x: int) -> int:\n    return x + 1\n"
        res1 = runner.run_pipeline(bad, goal="Add one")
        self.assertEqual(res1["status"], "FAIL_TIER0")

        # Local repair round
        fixed = runner.router.repair_local(bad, str(res1["msg"]))
        res2 = runner.run_pipeline(fixed, goal="Add one")
        self.assertEqual(res2["status"], "SUCCESS_LOCAL")

        # Fallback to micro packet
        ok_pk, pk = EscalateRouter.pack_payload("add", bad, "err", "fix")
        self.assertTrue(ok_pk)
        self.assertLessEqual(len(pk), 300)


if __name__ == "__main__":
    unittest.main()
