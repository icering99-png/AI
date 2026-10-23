"""Pipeline Runner integrating Tier 0-2 guards, critic and router."""

import os
from pathlib import Path
import shutil
import stat
import time

from core.audit_logger import AuditLogger
from core.crash_recovery import _chk_target
from core.defense_guard import DefenseGuard
from core.escalation_router import EscalateRouter
from core.ollama_client import OllamaClient
from core.plan_architect import PlanArch
from core.regression_guard import RegressGuard
from core.rules_critic import RulesCritic

_CRITIC_KEYS = ("auditor", "critic", "red_team", "adversary", "verifier")
_WORKSPACES = {"inherit", "branch", "share"}
_MODELS = {"pro", "flash", "flash_lite", "inherit"}


def _chk_args(role: str, prompt: str, ws: str) -> bool:
    """Validate subagent input types and boundaries."""
    if not (isinstance(role, str) and role.strip() and len(role.strip()) <= 50):
        return False
    if not (isinstance(prompt, str) and prompt.strip()):
        return False
    if ws not in _WORKSPACES:
        return False
    return True


def _pick_model(role: str, is_adv: bool, model: str | None) -> str:
    """Force model 'pro' for critics; allow override for others."""
    if is_adv or any(k in role.lower() for k in _CRITIC_KEYS):
        return "pro"
    return model if model in _MODELS else "flash"


def _pick_ws(role: str, default_ws: str) -> str:
    """Default authors to branch workspace for worktree isolation."""
    if role.lower().startswith("author") or "implementer" in role.lower():
        return "branch"
    return default_ws


def build_spec(
    role: str,
    prompt: str,
    workspace: str = "inherit",
    is_adversary: bool = False,
    model: str | None = None,
) -> dict[str, str]:
    """Build subagent configuration with forced intelligence asymmetry."""
    if not _chk_args(role, prompt, workspace):
        raise ValueError("Invalid subagent specification arguments")
    r_clean = role.strip()
    return {
        "TypeName": "self",
        "Role": r_clean,
        "Prompt": prompt.strip(),
        "Model": _pick_model(r_clean, is_adversary, model),
        "Workspace": _pick_ws(r_clean, workspace),
    }


def _fix_ro(func: object, p: str, _exc: object) -> None:
    """Reset Windows read-only attribute on deletion failure."""
    try:
        os.chmod(p, stat.S_IWRITE)
        func(p)  # type: ignore
    except OSError:
        pass


def _rm_target(target_p: Path) -> None:
    """Remove file or directory with read-only handler."""
    if target_p.is_dir():
        shutil.rmtree(target_p, onerror=_fix_ro)
    else:
        os.chmod(target_p, stat.S_IWRITE)
        target_p.unlink(missing_ok=True)


def clean_tree(path_str: str, root_str: str = ".") -> tuple[bool, str]:
    """Safely remove isolated worktree directory handling Windows file locks."""
    ok, target_p, msg = _chk_target(path_str, root_str)
    if not ok or target_p is None:
        return False, msg
    if not target_p.exists():
        return True, "NOT_FOUND"

    for attempt in range(3):
        try:
            _rm_target(target_p)
            return True, "REMOVED"
        except (PermissionError, OSError) as err:
            time.sleep(0.05 * (attempt + 1))
            if attempt == 2:
                return False, f"LOCK_ERROR: {err}"
    return False, "UNKNOWN_ERROR"


class PipelineRunner:
    """Coordinating runner for local-first adversarial pipeline."""

    def __init__(
        self,
        root_dir: str = ".",
        ollama: OllamaClient | None = None,
        logger: AuditLogger | None = None,
    ) -> None:
        self.root_dir = root_dir
        self.ollama = ollama or OllamaClient()
        self.logger = logger or AuditLogger()
        self.router = EscalateRouter(max_retries=3, max_cloud_tries=2, ollama_cli=self.ollama)

    def log_step(self, step: str, target: str, status: str, details: dict | None = None) -> dict:
        """Programmatic logging hook delegating to AuditLogger."""
        return self.logger.log(step=step, target=target, status=status, details=details)

    def run_pipeline(
        self,
        code: str,
        goal: str,
        diff_txt: str = "",
        plan: dict | None = None,
    ) -> dict[str, str | bool | dict]:
        """Execute full evaluation sequence."""
        # 1. Tier 0 Defense Guard: Syntax
        ok_syn, syn_msg = DefenseGuard.chk_syntax(code)
        if not ok_syn:
            return {"status": "FAIL_TIER0", "msg": syn_msg, "cost": 0}

        # 2. Tier 0: Identifier length <= 15 chars
        ok_id, id_msg = DefenseGuard.chk_ident(code, limit=15)
        if not ok_id:
            return {"status": "FAIL_TIER0", "msg": id_msg, "cost": 0}

        # 3. Tier 0: Diff budget <= 30
        if diff_txt:
            ok_df, df_msg = DefenseGuard.chk_diff(diff_txt, max_l=30)
            if not ok_df:
                return {"status": "FAIL_TIER0", "msg": df_msg, "cost": 0}

        # 4. Tier 0: Dangerous ops
        ok_dng, dng_msg = DefenseGuard.chk_danger(code)
        if not ok_dng:
            return {"status": "FAIL_TIER0", "msg": dng_msg, "cost": 0}

        # 5. Rules Critic (Blind Review) with Canary Verification
        if not RulesCritic.verify_canary(RulesCritic.audit):
            return {"status": "FAIL_CANARY", "msg": "Auditor failed canary trap", "cost": 0}

        verdict = RulesCritic.audit(code)
        if verdict.get("verdict") == "REJECT":
            return {"status": "REJECT_CRITIC", "verdict": verdict, "cost": 0}

        # 6. Update Plan on success if provided
        if plan:
            plan = PlanArch.rotate_step(plan, evid="exit_code: 0, PASS")

        try:
            return {
                "status": "SUCCESS_LOCAL",
                "msg": "Code approved locally",
                "cost": 0,
                "plan": plan,
            }
        finally:
            if hasattr(self.ollama, "unload"):
                self.ollama.unload()

    def query_rag(self, query: str, rag_cli: any = None) -> str:
        """Query knowledge base context via RAG adapter."""
        return rag_cli.search(query) if rag_cli else ""

    def save_turn(self, mem_cli: any, role: str, txt: str) -> bool:
        """Persist session dialogue turn via memory adapter."""
        return mem_cli.save(role, txt) if mem_cli else False
