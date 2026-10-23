"""Test suite for Tier 1 FastRouter."""
import time
import unittest
from core.fast_router import FastRouter


class TestFastRouter(unittest.TestCase):
    """Verify zero-token instant matching and latency."""

    def test_instant_match(self) -> None:
        """Ensure matches complete under 5ms with zero cost."""
        start = time.perf_counter()
        res = FastRouter.match("статус")
        elapsed = time.perf_counter() - start

        self.assertIsNotNone(res)
        self.assertEqual(res["intent"], "STATUS")
        self.assertEqual(res["cost"], "0")
        self.assertLess(elapsed, 0.005)

    def test_english_commands(self) -> None:
        """Verify English variants."""
        res_test = FastRouter.match("test")
        self.assertIsNotNone(res_test)
        self.assertEqual(res_test["intent"], "TEST")

        res_abort = FastRouter.match("rollback")
        self.assertIsNotNone(res_abort)
        self.assertEqual(res_abort["intent"], "ABORT")

    def test_fallback_on_code(self) -> None:
        """Ensure regular code or free text falls back."""
        res = FastRouter.match("def foo(): return 1")
        self.assertIsNone(res)
