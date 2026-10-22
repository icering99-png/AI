"""Unit tests for NetGuard outbox queue and connectivity guard."""

import os
import shutil
import tempfile
import time
import unittest
from unittest.mock import MagicMock

from core.net_guard import NetGuard


class TestNetGuard(unittest.TestCase):
    """Test suite for NetGuard."""

    def setUp(self) -> None:
        """Create temporary test directory."""
        self.tmp_dir = tempfile.mkdtemp()
        self.guard = NetGuard(root=self.tmp_dir, max_items=3, max_len=50)

    def tearDown(self) -> None:
        """Clean up temporary test directory."""
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def test_enqueue_len_exceeded(self) -> None:
        """Verify Gate 8 payload length enforcement."""
        large_p = {"msg": "x" * 60}
        res = self.guard.enqueue(large_p)
        self.assertFalse(res["ok"])
        self.assertEqual(res["err"], "len_exceeded")

    def test_enqueue_queue_full(self) -> None:
        """Verify queue capacity limit and explicit failure."""
        for i in range(3):
            res = self.guard.enqueue({"i": i})
            self.assertTrue(res["ok"])
        res_full = self.guard.enqueue({"i": 4})
        self.assertFalse(res_full["ok"])
        self.assertEqual(res_full["err"], "queue_full")

    def test_poll_idle_no_network(self) -> None:
        """Verify empty queue does not touch network."""
        self.guard.chk_online = MagicMock()
        res = self.guard.poll_step(lambda p: True)
        self.assertEqual(res["status"], "idle")
        self.assertEqual(res["sent"], 0)
        self.guard.chk_online.assert_not_called()

    def test_poll_offline(self) -> None:
        """Verify offline state leaves packets in queue."""
        self.guard.enqueue({"test": 1})
        self.guard.chk_online = MagicMock(return_value=False)
        send_mock = MagicMock()
        res = self.guard.poll_step(send_mock)
        self.assertEqual(res["status"], "offline")
        self.assertEqual(res["sent"], 0)
        send_mock.assert_not_called()
        self.assertTrue(self.guard.has_pending())

    def test_poll_online_success(self) -> None:
        """Verify successful online delivery cleans up outbox."""
        self.guard.enqueue({"test": 1})
        self.guard.chk_online = MagicMock(return_value=True)
        res = self.guard.poll_step(lambda p: True)
        self.assertEqual(res["status"], "online")
        self.assertEqual(res["sent"], 1)
        self.assertFalse(self.guard.has_pending())

    def test_poll_send_fail_rollback(self) -> None:
        """Verify send failure rolls back inflight file to json."""
        self.guard.enqueue({"test": 1})
        self.guard.chk_online = MagicMock(return_value=True)
        res = self.guard.poll_step(lambda p: False)
        self.assertEqual(res["status"], "online")
        self.assertEqual(res["sent"], 0)
        self.assertTrue(self.guard.has_pending())
        # verify no dangling inflight files
        files = os.listdir(self.tmp_dir)
        self.assertTrue(any(f.endswith(".json") for f in files))
        self.assertFalse(any(f.endswith(".inflight") for f in files))

    def test_rec_inflight(self) -> None:
        """Verify crash recovery renames old inflight file to json."""
        p_fly = os.path.join(self.tmp_dir, "pkt_123.inflight")
        with open(p_fly, "w", encoding="utf-8") as f:
            f.write("{}")
        past = time.time() - 100
        os.utime(p_fly, (past, past))

        rec_cnt = self.guard.rec_inflight(max_age=50)
        self.assertEqual(rec_cnt, 1)
        self.assertTrue(os.path.exists(os.path.join(self.tmp_dir, "pkt_123.json")))

    def test_purge_old(self) -> None:
        """Verify purge of expired packets based on TTL."""
        p_json = os.path.join(self.tmp_dir, "pkt_old.json")
        with open(p_json, "w", encoding="utf-8") as f:
            f.write("{}")
        past = time.time() - 200
        os.utime(p_json, (past, past))

        del_cnt = self.guard.purge_old(ttl_sec=100)
        self.assertEqual(del_cnt, 1)
        self.assertFalse(os.path.exists(p_json))


if __name__ == "__main__":
    unittest.main()
