"""Blind Rules Critic adhering to schemas/critic_verdict.json."""

import json
from pathlib import Path


class RulesCritic:
    """Independent logic auditor. Never repairs code directly."""

    @staticmethod
    def make_pass() -> dict[str, str]:
        """Construct valid PASS verdict."""
        return {"verdict": "PASS"}

    @staticmethod
    def make_reject(rule: str, evid: str, req: str) -> dict[str, str]:
        """Construct valid REJECT verdict."""
        return {
            "verdict": "REJECT",
            "rule_id": rule,
            "evidence": evid,
            "required_change": req,
        }

    @staticmethod
    def check_fail_idx(text: str, path_str: str) -> tuple[bool, str]:
        """Check text against failure_index.json disproven prohibitions."""
        p = Path(path_str).resolve()
        if not p.exists():
            return True, "OK"

        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data.get("failures", []):
                proh = item.get("prohibition", "")
                symp = item.get("symptom", "")
                if symp and symp.lower() in text.lower():
                    return False, f"Known fail {item.get('id')}: {proh}"
            return True, "OK"
        except (json.JSONDecodeError, OSError) as err:
            return False, f"Index read error: {err}"

    @staticmethod
    def verify_canary(critic_fn) -> bool:
        """Run canary trap with known broken snippet. Must return REJECT."""
        trap_code = "eval('dangerous_call()')"
        verdict = critic_fn(trap_code)
        return verdict.get("verdict") == "REJECT"

    @classmethod
    def audit(
        cls,
        code: str,
        fail_path: str = "failure_index.json",
        touch_path: str = "",
        allow_test_edit: bool = False,
        approve_token: str = "",
    ) -> dict[str, str]:
        """Audit code blindly against core rules, fail index, and R002 backstop."""
        from core.defense_guard import DefenseGuard

        if touch_path:
            ok_p, msg_p = DefenseGuard.chk_protected(touch_path, allow_test_edit, approve_token)
            if not ok_p:
                return cls.make_reject("R002", msg_p, "Oracle tests/schemas immutable")

        ok_dng, dng_msg = DefenseGuard.chk_danger(code)
        if not ok_dng:
            return cls.make_reject("R001", dng_msg, "Remove forbidden dynamic/destructive calls")

        ok, msg = cls.check_fail_idx(code, fail_path)
        if not ok:
            return cls.make_reject("GATE-10", msg, "Do not repeat known failure")

        return cls.make_pass()
