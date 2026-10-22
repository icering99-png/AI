"""Unit tests for structured LLM output and semantic template memory."""

import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock

from core.ollama_client import OllamaClient
from core.semantic_memory import SemanticMemory


class TestLlmCore(unittest.TestCase):
    """Test suite for Ollama structured JSON and SemanticMemory."""

    def setUp(self) -> None:
        """Create temporary directory for template storage."""
        self.tmp_dir = tempfile.mkdtemp()
        self.memory = SemanticMemory(root=self.tmp_dir)

    def tearDown(self) -> None:
        """Clean up temporary directory."""
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def test_gen_json_valid_keys(self) -> None:
        """Verify gen_json passes when all schema keys exist."""
        client = OllamaClient()
        client.generate = MagicMock(return_value='{"verdict": "PASS", "rule": "R01"}')
        res = client.gen_json("prompt", keys=["verdict", "rule"])
        self.assertTrue(res["ok"])
        self.assertEqual(res["data"]["verdict"], "PASS")

    def test_gen_json_missing_keys(self) -> None:
        """Verify gen_json fails when required schema keys are missing."""
        client = OllamaClient()
        client.generate = MagicMock(return_value='{"verdict": "PASS"}')
        res = client.gen_json("prompt", keys=["verdict", "evidence"])
        self.assertFalse(res["ok"])
        self.assertIn("miss", str(res["err"]))

    def test_gen_json_not_dict(self) -> None:
        """Verify gen_json fails when output is JSON list."""
        client = OllamaClient()
        client.generate = MagicMock(return_value='[1, 2, 3]')
        res = client.gen_json("prompt")
        self.assertFalse(res["ok"])
        self.assertEqual(res["err"], "not_dict")

    def test_gen_json_bad_syntax(self) -> None:
        """Verify gen_json fails on broken non-JSON text."""
        client = OllamaClient()
        client.generate = MagicMock(return_value="Plain text greeting")
        res = client.gen_json("prompt")
        self.assertFalse(res["ok"])
        self.assertIsNotNone(res["err"])

    def test_semantic_save_and_get(self) -> None:
        """Verify valid template save and retrieval."""
        code = "def add(a: int, b: int) -> int:\n    return a + b\n"
        ok = self.memory.save_tmpl("math", "add", code)
        self.assertTrue(ok)
        loaded = self.memory.get_tmpl("math", "add")
        self.assertEqual(loaded, code)

    def test_semantic_syntax_fail(self) -> None:
        """Verify broken syntax rejected upon save."""
        bad_code = "def broken(:\n    return"
        ok = self.memory.save_tmpl("math", "bad", bad_code)
        self.assertFalse(ok)
        self.assertIsNone(self.memory.get_tmpl("math", "bad"))

    def test_semantic_tamper_guard(self) -> None:
        """Verify modified file triggers hash mismatch and Fail-Closed."""
        code = "def ok() -> str:\n    return 'safe'\n"
        self.assertTrue(self.memory.save_tmpl("sys", "ok", code))
        path = os.path.join(self.tmp_dir, "sys", "ok.json")
        with open(path, "r", encoding="utf-8") as f:
            rec = json.load(f)
        rec["code"] = "def ok() -> str:\n    return 'tampered'\n"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rec, f)
        self.assertIsNone(self.memory.get_tmpl("sys", "ok"))


if __name__ == "__main__":
    unittest.main()
