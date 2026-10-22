"""Unit tests for RunbookGen deployment specifications."""

import os
import shutil
import tempfile
import unittest

from core.runbook_gen import RunbookGen


class TestRunbookGen(unittest.TestCase):
    """Test suite for runbook generation and verification."""

    def setUp(self) -> None:
        """Create temporary test environment."""
        self.tmp_dir = tempfile.mkdtemp()
        self.gen = RunbookGen()

        self.fn_file = os.path.join(self.tmp_dir, "mod_fn.py")
        with open(self.fn_file, "w", encoding="utf-8") as f:
            f.write("def entry_fn(x: int) -> int:\n    return x + 1\n")

        self.cls_file = os.path.join(self.tmp_dir, "mod_cls.py")
        with open(self.cls_file, "w", encoding="utf-8") as f:
            f.write("class EntryClass:\n    pass\n")

        self.spec_p = os.path.join(self.tmp_dir, "runbook.json")

    def tearDown(self) -> None:
        """Clean up temporary test environment."""
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def test_entry_function(self) -> None:
        """Verify function entry point detection and spec creation."""
        res = self.gen.gen_spec(
            mod="test_fn",
            files=[self.fn_file],
            entry="entry_fn",
            envs=["ENV_1"],
            cmd="pytest",
            out_p=self.spec_p,
            sem_key="math_add",
        )
        self.assertTrue(res["ok"])
        self.assertEqual(res["spec"]["kind"], "function")
        self.assertEqual(res["spec"]["status"], "VERIFIED")

    def test_entry_class(self) -> None:
        """Verify class entry point detection and spec creation."""
        res = self.gen.gen_spec(
            mod="test_cls",
            files=[self.cls_file],
            entry="EntryClass",
            envs=[],
            cmd="python test.py",
            out_p=self.spec_p,
        )
        self.assertTrue(res["ok"])
        self.assertEqual(res["spec"]["kind"], "class")

    def test_entry_missing(self) -> None:
        """Verify failure when entry point is absent from AST."""
        res = self.gen.gen_spec(
            mod="test_miss",
            files=[self.fn_file],
            entry="non_existent_fn",
            envs=[],
            cmd="pytest",
            out_p=self.spec_p,
        )
        self.assertFalse(res["ok"])
        self.assertIn("entry_missing", res["err"])

    def test_missing_file(self) -> None:
        """Verify failure when artifact file does not exist."""
        res = self.gen.gen_spec(
            mod="test_none",
            files=[os.path.join(self.tmp_dir, "missing.py")],
            entry="fn",
            envs=[],
            cmd="pytest",
            out_p=self.spec_p,
        )
        self.assertFalse(res["ok"])
        self.assertIn("missing_file", res["err"])

    def test_verify_spec_ok(self) -> None:
        """Verify valid spec verification returns ok."""
        self.gen.gen_spec("mod", [self.fn_file], "entry_fn", [], "run", self.spec_p)
        chk = self.gen.verify_spec(self.spec_p)
        self.assertTrue(chk["ok"])
        self.assertEqual(chk["reason"], "ok")

    def test_hash_mismatch_and_update(self) -> None:
        """Verify detection of file edit and subsequent update_spec."""
        self.gen.gen_spec("mod", [self.fn_file], "entry_fn", [], "run", self.spec_p)

        with open(self.fn_file, "a", encoding="utf-8") as f:
            f.write("# edited line\n")

        chk1 = self.gen.verify_spec(self.spec_p)
        self.assertFalse(chk1["ok"])
        self.assertEqual(chk1["reason"], "hash_mismatch")

        # Without token -> must be rejected
        up_fail = self.gen.update_spec(self.spec_p, approve_token="")
        self.assertFalse(up_fail)

        # With valid token -> must succeed
        up_ok = self.gen.update_spec(self.spec_p, approve_token="APPROVE SUB-04")
        self.assertTrue(up_ok)

        chk2 = self.gen.verify_spec(self.spec_p)
        self.assertTrue(chk2["ok"])
        self.assertEqual(chk2["reason"], "ok")

    def test_file_missing_on_verify(self) -> None:
        """Verify detection when artifact is deleted after spec creation."""
        self.gen.gen_spec("mod", [self.fn_file], "entry_fn", [], "run", self.spec_p)
        os.remove(self.fn_file)
        chk = self.gen.verify_spec(self.spec_p)
        self.assertFalse(chk["ok"])
        self.assertEqual(chk["reason"], "file_missing")


if __name__ == "__main__":
    unittest.main()
