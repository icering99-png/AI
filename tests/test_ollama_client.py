"""Unit tests for local Ollama client lifecycle and VRAM management."""
import re
import unittest
from core.ollama_client import OllamaClient


class TestOllamaClient(unittest.TestCase):
    """Test suite verifying local Ollama client integration."""

    def setUp(self) -> None:
        self.client = OllamaClient(model="qwen2.5-coder:1.5b")

    def test_lifecycle(self) -> None:
        """Verify generation, VRAM presence, and explicit unload."""
        en_text = "Status: all systems operational."
        ru_text = self.client.translate(en_text)
        self.assertIsInstance(ru_text, str)
        self.assertGreater(len(ru_text), 0)

        # Check loaded models in VRAM
        loaded = self.client.get_loaded()
        self.assertIsInstance(loaded, list)

        # Test unload from VRAM
        unloaded = self.client.unload()
        self.assertTrue(unloaded)

    def test_think_strip(self) -> None:
        """Verify that reasoning tags are stripped cleanly."""
        raw = "<think>\nThinking about code...\n</think>\ndef test() -> int:\n    return 1"
        cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        self.assertEqual(cleaned, "def test() -> int:\n    return 1")

    def test_resource_guard_thresholds(self) -> None:
        """Verify that pre-flight checks block overloaded system."""
        # Low VRAM rejection
        self.client.min_vram_mib = 99999
        ok_vram, msg_vram = self.client.chk_resources()
        self.assertFalse(ok_vram)
        self.assertIn("INSUFFICIENT_VRAM", msg_vram)
        self.client.min_vram_mib = 100

        # Low RAM rejection
        self.client.min_ram_mib = 999999
        ok_ram, msg_ram = self.client.chk_resources()
        self.assertFalse(ok_ram)
        self.assertIn("INSUFFICIENT_RAM", msg_ram)
        self.client.min_ram_mib = 100

        # CPU overloaded rejection
        self.client.max_cpu_pct = -1.0
        ok_cpu, msg_cpu = self.client.chk_resources()
        self.assertFalse(ok_cpu)
        self.assertIn("CPU_THROTTLED", msg_cpu)
        self.client.max_cpu_pct = 95.0

        # Normal condition passes
        ok_norm, msg_norm = self.client.chk_resources()
        self.assertTrue(ok_norm)
        self.assertEqual(msg_norm, "OK")


if __name__ == "__main__":
    unittest.main()
