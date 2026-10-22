"""Comprehensive end-to-end test suite for the local adversarial core."""

import unittest
from pathlib import Path

from core.defense_guard import DefenseGuard
from core.escalation_router import EscalateRouter
from core.plan_architect import PlanArch
from core.regression_guard import RegressGuard
from core.rules_critic import RulesCritic
from core.runner import PipelineRunner
from core.subplan_decomposer import SubplanDec


class TestLocalPipeline(unittest.TestCase):
    """End-to-end pipeline validation suite."""

    def setUp(self):
        self.runner = PipelineRunner()
        self.root = Path(__file__).resolve().parent.parent

    def test_01_green_path_zero_tokens(self):
        """Valid compliant code succeeds with 0 token cloud cost."""
        code = "def calc(num: int) -> int:\n    return num * 2\n"
        diff = "+ def calc(num: int) -> int:\n+     return num * 2\n"
        res = self.runner.run_pipeline(code, goal="Double number", diff_txt=diff)
        self.assertEqual(res["status"], "SUCCESS_LOCAL")
        self.assertEqual(res["cost"], 0)

    def test_02_defense_guard_rejects_long_name(self):
        """Identifier > 15 chars is rejected at Tier 0."""
        code = "def calculate_total_amount(val: int) -> int:\n    return val\n"
        res = self.runner.run_pipeline(code, goal="Calc total")
        self.assertEqual(res["status"], "FAIL_TIER0")
        self.assertIn("calculate_total", str(res["msg"]))

    def test_03_defense_guard_rejects_danger(self):
        """Banned dynamic execution is rejected at Tier 0."""
        code = "def run_dyn(cmd: str):\n    eval(cmd)\n"
        res = self.runner.run_pipeline(code, goal="Run dynamic")
        self.assertEqual(res["status"], "FAIL_TIER0")
        self.assertIn("Banned", str(res["msg"]))

    def test_04_rules_critic_blind_reject(self):
        """Rules Critic returns schema-compliant REJECT verdict."""
        verdict = RulesCritic.audit("x = eval('1+1')")
        self.assertEqual(verdict.get("verdict"), "REJECT")
        self.assertEqual(verdict.get("rule_id"), "R001")
        self.assertIn("evidence", verdict)
        self.assertIn("required_change", verdict)

    def test_05_canary_trap_detection(self):
        """Canary trap correctly detects non-sleeping critic."""
        passed = RulesCritic.verify_canary(RulesCritic.audit)
        self.assertTrue(passed)

    def test_06_plan_architect_and_decomposer(self):
        """Tasks are quantized into <= 30 diff subplans and archived."""
        tasks = ["Setup DB", "Create models", "Add routes"]
        subs = SubplanDec.decompose(tasks)
        self.assertEqual(len(subs), 3)

        ok_dag, msg = SubplanDec.validate_dag(subs)
        self.assertTrue(ok_dag)

        plan = PlanArch.init_plan("Build REST API", subs)
        self.assertEqual(plan["active"]["id"], "SUB-01")

        # Rotate step 1
        plan = PlanArch.rotate_step(plan, evid="exit_code: 0")
        self.assertEqual(len(plan["archive"]), 1)
        self.assertEqual(plan["archive"][0]["id"], "SUB-01")
        self.assertEqual(plan["active"]["id"], "SUB-02")

        md = PlanArch.render_md(plan)
        self.assertIn("АРХИВ ВЫПОЛНЕННЫХ ШАГОВ", md)
        self.assertIn("SUB-01", md)

    def test_07_escalation_micro_packet_limit(self):
        """Escalation micro-packet stays strictly <= 300 chars."""
        goal = "Fix vector norm division by zero"
        code = "norm = np.linalg.norm(v)\nres = v / norm"
        err = "ZeroDivisionError in line 42"
        want = "res = v / (norm + 1e-9)"

        ok, payload = EscalateRouter.pack_payload(goal, code, err, want)
        self.assertTrue(ok)
        self.assertLessEqual(len(payload), 300)

        router = EscalateRouter(max_retries=3, max_cloud_tries=2)
        ok_cloud, msg = router.request_cloud(payload)
        self.assertTrue(ok_cloud)

        # Exceed limit
        router.request_cloud(payload)
        ok_third, third_msg = router.request_cloud(payload)
        self.assertFalse(ok_third)
        self.assertIn("FAIL_CLOSED", third_msg)

    def test_08_regression_manifest_integrity(self):
        """State manifest detects file drift and unauthorized modifications."""
        target_f = self.root / "core" / "defense_guard.py"
        manifest_f = self.root / "state_manifest.json"

        ok_save = RegressGuard.save_manifest([str(target_f)], str(manifest_f))
        self.assertTrue(ok_save)

        ok_chk, drifted = RegressGuard.chk_manifest(str(manifest_f))
        self.assertTrue(ok_chk)
    def test_09_subplan_fission(self):
        """Stuck subplan splits into two atomic micro-steps under half diff limit."""
        sub = {"id": "SUB-09", "title": "Complex DB Migration", "max_diff": 30}
        sub_a, sub_b = SubplanDec.fission_step(sub)
        self.assertEqual(sub_a["id"], "SUB-09a")
        self.assertEqual(sub_b["id"], "SUB-09b")
        self.assertEqual(sub_a["max_diff"], 15)
        self.assertEqual(sub_b["max_diff"], 15)
        self.assertIn("Part 1", str(sub_a["title"]))
        self.assertIn("Part 2", str(sub_b["title"]))

    def test_10_dag_topology_validation(self):
        """DAG topology correctly validates sequential and detects broken order."""
        tasks = ["Setup DB", "Create models"]
        subs = SubplanDec.decompose(tasks)
        ok, msg = SubplanDec.validate_dag(subs)
        self.assertTrue(ok)
        self.assertEqual(subs[1]["depends_on"], "SUB-01")

        broken = [
            {"id": "SUB-02", "max_diff": 15, "depends_on": "SUB-01"},
            {"id": "SUB-01", "max_diff": 15, "depends_on": None},
        ]
        ok_b, msg_b = SubplanDec.validate_dag(broken)
        self.assertFalse(ok_b)
        self.assertIn("Broken DAG", msg_b)

    def test_11_defense_guard_get_defs(self):
        """Verify DefenseGuard.get_defs extracts functions and classes."""
        code = "def foo(): pass\nasync def bar(): pass\nclass Baz: pass\nx = 1\n"
        defs = DefenseGuard.get_defs(code)
        self.assertEqual(len(defs), 3)
        self.assertIn(("foo", "function"), defs)
        self.assertIn(("bar", "function"), defs)
        self.assertIn(("Baz", "class"), defs)


if __name__ == "__main__":
    unittest.main()
