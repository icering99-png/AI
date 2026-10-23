"""Unit tests for EscalateRouter local repair and cloud limits."""
import unittest
from core.escalation_router import EscalateRouter


class MockOllama:
    """Mock local LLM returning fixed code."""
    def generate(self, prompt: str) -> str:
        return "def fixed(): return 42"


class TestEscalateRouter(unittest.TestCase):
    """Test suite verifying local retry and escalation limits."""

    def test_local_repair_with_mock(self) -> None:
        """Verify local repair via OllamaClient integration."""
        router = EscalateRouter(max_retries=2, ollama_cli=MockOllama())
        self.assertTrue(router.can_retry_local())
        fix = router.repair_local("def broken(): pass", "SyntaxError")
        self.assertEqual(fix, "def fixed(): return 42")
        self.assertEqual(router.local_retries, 1)

    def test_local_retry_exhaustion(self) -> None:
        """Verify local retry stops after reaching max_retries limit."""
        router = EscalateRouter(max_retries=1, ollama_cli=MockOllama())
        router.repair_local("code", "err")
        self.assertFalse(router.can_retry_local())
        fix2 = router.repair_local("code", "err")
        self.assertEqual(fix2, "")


    def test_model_tier_escalation(self) -> None:
        """Verify model escalated through 1.5b -> 3b -> 7b."""
        mock = MockOllama()
        router = EscalateRouter(max_retries=3, ollama_cli=mock)
        self.assertEqual(router.get_tier_model(), "qwen2.5-coder:1.5b")
        router.repair_local("c1", "e1")
        self.assertEqual(router.get_tier_model(), "qwen2.5-coder:3b")
        router.repair_local("c2", "e2")
        self.assertEqual(router.get_tier_model(), "qwen2.5-coder:7b")


    def test_guidance_cache(self) -> None:
        """Verify cache save and retrieve roundtrip."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            fpath = tf.name
        self.assertIsNone(EscalateRouter.get_cache("err_key", fpath))
        self.assertTrue(EscalateRouter.save_cache("err_key", "fix_sol", fpath))
        self.assertEqual(EscalateRouter.get_cache("err_key", fpath), "fix_sol")

    def test_split_patch_chunking(self) -> None:
        """Verify large cloud patches split into testable chunks under budget."""
        small = "line 1\nline 2"
        self.assertEqual(len(EscalateRouter.split_patch(small, chunk_size=30)), 1)
        large = "\n".join([f"+ code line {i}" for i in range(75)])
        chunks = EscalateRouter.split_patch(large, chunk_size=30)
        self.assertEqual(len(chunks), 3)
        self.assertEqual(len(chunks[0].splitlines()), 30)
        self.assertEqual(len(chunks[1].splitlines()), 30)
        self.assertEqual(len(chunks[2].splitlines()), 15)


if __name__ == "__main__":
    unittest.main()
