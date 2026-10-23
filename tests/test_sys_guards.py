"""Unit tests for Windows system guards, bin resolver, and metric integrity."""

import os
import tempfile
import unittest

from core.artifact_guard import (
    FailClosedErr,
    check_metric,
    run_fallback,
    safe_calc,
    verify_file,
)

from core.bin_resolver import resolve_bin
from core.defense_guard import DefenseGuard


class TestSysGuards(unittest.TestCase):
    """Test suite for system resolution and artifact guards."""

    def test_bin_resolver_existing(self) -> None:
        """Verify standard system binary resolution."""
        res = resolve_bin("cmd")
        self.assertIsNotNone(res)
        if res:
            self.assertTrue(os.path.isfile(res))

    def test_bin_resolver_missing(self) -> None:
        """Verify non-existent binary resolution returns None."""
        res = resolve_bin("missing_binary_random_xyz_123")
        self.assertIsNone(res)

    def test_verify_file_missing(self) -> None:
        """Verify missing path returns False."""
        self.assertFalse(verify_file("missing_path_xyz_123.tmp"))

    def test_verify_file_empty(self) -> None:
        """Verify 0-byte file returns False for min_sz >= 1."""
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            p = tf.name
        try:
            self.assertFalse(verify_file(p, min_sz=1))
        finally:
            if os.path.exists(p):
                os.remove(p)

    def test_verify_file_valid(self) -> None:
        """Verify populated file returns True."""
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            p = tf.name
        try:
            with open(p, "wb") as f:
                f.write(b"content")
            self.assertTrue(verify_file(p, min_sz=1))
            self.assertFalse(verify_file(p, min_sz=100))
        finally:
            if os.path.exists(p):
                os.remove(p)

    def test_check_metric_ok(self) -> None:
        """Verify valid metric returns value."""
        self.assertEqual(check_metric(100, "cov"), 100)
        self.assertEqual(check_metric(0.0, "time"), 0.0)

    def test_check_metric_fail(self) -> None:
        """Verify null metric raises FailClosedErr."""
        with self.assertRaises(FailClosedErr):
            check_metric(None, "vram")

    def test_defense_canary(self) -> None:
        """Verify DefenseGuard canary self-test operates correctly."""
        guard = DefenseGuard()
        self.assertTrue(guard.self_test())


    def test_safe_calc(self) -> None:
        """Verify calculation audit record without validation theater."""
        rec_ok = safe_calc(lambda x: x * 2, 21, name="double")
        self.assertTrue(rec_ok["ok"])
        self.assertEqual(rec_ok["val"], 42)

        rec_null = safe_calc(lambda: None, name="empty")
        self.assertFalse(rec_null["ok"])
        self.assertIsNone(rec_null["val"])
        self.assertEqual(rec_null["err"], "null_res")

        def broken():
            raise ValueError("err_calc")

        rec_err = safe_calc(broken, name="err")
        self.assertFalse(rec_err["ok"])
        self.assertIn("err_calc", rec_err["err"])

    def test_run_fallback(self) -> None:
        """Verify seamless pure-Python fallback execution."""
        def primary_fail():
            raise RuntimeError("C library failed")

        def fallback_ok():
            return "pure_python_ok"

        res = run_fallback(primary_fail, fallback_ok)
        self.assertEqual(res, "pure_python_ok")

        res_direct = run_fallback(lambda: "direct_ok", fallback_ok)
        self.assertEqual(res_direct, "direct_ok")

    def test_canonical_hashing(self) -> None:
        """Verify canonical file and string SHA-256 calculation."""
        from core.artifact_guard import hash_file, hash_str
        self.assertEqual(hash_file("nonexistent_file_xyz.tmp"), "")
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(b"canonical_hash_test")
            tf_path = tf.name
        try:
            h_f = hash_file(tf_path, chunk_size=65536)
            h_s = hash_str("canonical_hash_test")
            self.assertEqual(h_f, h_s)
            self.assertEqual(len(h_f), 64)
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)


if __name__ == "__main__":
    unittest.main()

