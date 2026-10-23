"""Unit tests for TrustedFetch module with positive and negative probes."""

import hashlib
import unittest
from core.trusted_fetch import TrustedFetch


class TestTrustedFetch(unittest.TestCase):
    """Test suite covering allowlist, SHA-256, AST safety, and quotas."""

    def setUp(self) -> None:
        """Reset limits before each test run."""
        TrustedFetch.reset_limits()

    def test_positive_valid_code_pass(self) -> None:
        """Positive test: verified code from allowlist with valid SHA-256 passes."""
        url = "https://raw.githubusercontent.com/org/repo/main/math_util.py"
        code = b"def calc_sum(a: int, b: int) -> int:\n    return a + b\n"
        sha = hashlib.sha256(code).hexdigest()
        ok, msg = TrustedFetch.verify_payload(url, code, sha)
        self.assertTrue(ok)
        self.assertEqual(msg, "OK")

    def test_reject_untrusted_host(self) -> None:
        """Negative test: untrusted domain blocked with ESCAPE_ATTEMPT."""
        url = "https://evil-site.com/hack.py"
        code = b"x = 1\n"
        sha = hashlib.sha256(code).hexdigest()
        ok, msg = TrustedFetch.verify_payload(url, code, sha)
        self.assertFalse(ok)
        self.assertIn("ESCAPE_ATTEMPT", msg)

    def test_reject_size_exceeded(self) -> None:
        """Negative test: payload exceeding 50 KB code limit is blocked."""
        url = "https://raw.githubusercontent.com/org/repo/main/big.py"
        code = b"# " + b"A" * (51 * 1024)
        sha = hashlib.sha256(code).hexdigest()
        ok, msg = TrustedFetch.verify_payload(url, code, sha)
        self.assertFalse(ok)
        self.assertIn("Size", msg)

    def test_reject_hash_mismatch(self) -> None:
        """Negative test: hash mismatch is blocked."""
        url = "https://raw.githubusercontent.com/org/repo/main/sample.py"
        code = b"def foo() -> int:\n    return 42\n"
        wrong_sha = "e" * 64
        ok, msg = TrustedFetch.verify_payload(url, code, wrong_sha)
        self.assertFalse(ok)
        self.assertIn("Hash mismatch", msg)

    def test_reject_dangerous_eval(self) -> None:
        """Negative test: code containing eval/exec blocked by AST defense."""
        url = "https://raw.githubusercontent.com/org/repo/main/unsafe.py"
        code = b"def run_bad():\n    eval('2+2')\n"
        sha = hashlib.sha256(code).hexdigest()
        ok, msg = TrustedFetch.verify_payload(url, code, sha)
        self.assertFalse(ok)
        self.assertIn("Banned: eval", msg)

    def test_quota_plan_limit(self) -> None:
        """Negative test: quota limit per plan (max 3) enforced."""
        url = "https://raw.githubusercontent.com/org/repo/main/stub.py"
        code = b"def ok_stub():\n    return 0\n"
        sha = hashlib.sha256(code).hexdigest()
        for _ in range(3):
            ok, _ = TrustedFetch.verify_payload(url, code, sha)
            self.assertTrue(ok)
        ok_lim, msg = TrustedFetch.chk_limits()
        self.assertFalse(ok_lim)
        self.assertIn("plan limit", msg)


if __name__ == "__main__":
    unittest.main()
