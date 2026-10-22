# tests/test_turn_guard.py
"""Unit tests for TurnGuard git turn and plan validation."""
import unittest
from core.turn_guard import TurnGuard


class TestTurnGuard(unittest.TestCase):
    """Test TurnGuard git diff validation against active plan step."""

    def setUp(self) -> None:
        self.plan = (
            "# Plan\n"
            "## Active Step\n"
            "* **ID:** `SUB-01`\n"
            "* **Target File:** `core/sample.py`\n"
        )

    def test_01_match_ok(self) -> None:
        """Target file strictly matching active step is approved."""
        ok, msg = TurnGuard.chk_diff(["core/sample.py"], self.plan)
        self.assertTrue(ok)
        self.assertIn("strictly matched", msg)

    def test_02_mismatch_blocked(self) -> None:
        """Unrelated file modification is blocked."""
        ok, msg = TurnGuard.chk_diff(["core/other.py"], self.plan)
        self.assertFalse(ok)
        self.assertIn("does not match active", msg)

    def test_03_budget_exceeded_blocked(self) -> None:
        """Multiple targets exceeding 1 file per turn are blocked."""
        ok, msg = TurnGuard.chk_diff(["core/sample.py", "core/sample.py/extra"], self.plan)
        self.assertFalse(ok)
        self.assertIn("BLOCKED", msg)

    def test_04_no_active_step_blocked(self) -> None:
        """Missing active step in plan triggers fail-closed block."""
        ok, msg = TurnGuard.chk_diff(["core/sample.py"], "# Empty plan")
        self.assertFalse(ok)
        self.assertIn("No active step found", msg)


if __name__ == "__main__":
    unittest.main()
