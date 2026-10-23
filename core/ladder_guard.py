"""Software Maturity Verification Ladder aggregating existing core guards."""

import os
from typing import Any, Dict, Optional

from core.artifact_guard import verify_file
from core.defense_guard import DefenseGuard
from core.rules_critic import RulesCritic
from core.runbook_gen import RunbookGen


class LadderGuard:
    """Evaluate and certify software maturity levels (L0 to L4)."""

    @staticmethod
    def eval_file(code_p: str, spec_p: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate artifact maturity level using existing guards."""
        if not verify_file(code_p):
            return {"level": 0, "name": "L0_NONE", "reason": "file_missing"}

        try:
            with open(code_p, "r", encoding="utf-8") as f:
                code = f.read()
        except Exception as exc:
            return {"level": 0, "name": "L0_NONE", "reason": str(exc)}

        ok_s, msg_s = DefenseGuard.chk_syntax(code)
        if not ok_s:
            return {"level": 0, "name": "L0_NONE", "reason": msg_s}

        ok_i, _ = DefenseGuard.chk_ident(code, limit=15)
        ok_d, _ = DefenseGuard.chk_danger(code)
        if not (ok_i and ok_d):
            return {"level": 1, "name": "L1_SYNTAX", "reason": "guard_limit"}

        if spec_p:
            res_spec = RunbookGen().verify_spec(spec_p)
            if not res_spec.get("ok"):
                return {"level": 2, "name": "L2_GUARDED", "reason": "spec_fail"}

        verdict = RulesCritic.audit(code)
        if verdict.get("verdict") != "PASS":
            cur_l = 3 if spec_p else 2
            cur_n = "L3_RUNBOOK" if spec_p else "L2_GUARDED"
            return {"level": cur_l, "name": cur_n, "reason": "critic_reject"}

        final_l = 4 if spec_p else 3
        final_n = "L4_CERTIFIED" if spec_p else "L3_CRITIC_OK"
        return {"level": final_l, "name": final_n, "reason": "ok"}
