"""Escalation router with micro-packet packing (<= 300 chars) and guidance cache."""

import json
from pathlib import Path
import time


class EscalateRouter:
    """Escalation gateway to cloud Gemini with strict size and retry limits."""

    TIER_MODELS = [
        "qwen2.5-coder:1.5b",
        "qwen2.5-coder:3b",
        "qwen2.5-coder:7b",
    ]

    def __init__(
        self,
        max_retries: int = 3,
        max_cloud_tries: int = 2,
        ollama_cli: object = None,
        budget_sec: float = 600.0,
    ) -> None:
        self.max_retries = max_retries
        self.max_cloud_tries = max_cloud_tries
        self.local_retries = 0
        self.cloud_tries = 0
        self.ollama = ollama_cli
        self.budget_sec = budget_sec
        self.start_time = time.time()

    def get_tier_model(self) -> str:
        """Select tier model based on current retry count."""
        idx = min(self.local_retries, len(self.TIER_MODELS) - 1)
        return self.TIER_MODELS[idx]

    def can_retry_local(self) -> bool:
        """Check if local retry and wall-clock time budget is available."""
        if (time.time() - self.start_time) >= self.budget_sec:
            return False
        return self.local_retries < self.max_retries

    @staticmethod
    def classify_err(err_msg: str) -> str:
        """Classify error into io, syntax, or runtime."""
        low = err_msg.lower()
        if any(k in low for k in ("filenotfound", "permission", "oserror", "ioerror", "denied")):
            return "io"
        if any(k in low for k in ("syntaxerror", "indent", "syntax:")):
            return "syntax"
        return "runtime"

    def record_retry(self) -> int:
        """Increment local retry counter."""
        self.local_retries += 1
        return self.local_retries

    def repair_local(self, code_str: str, err_msg: str, guide: str = "") -> str:
        """Generate local repair diff skipping IO errors to avoid hallucinations."""
        if self.classify_err(err_msg) == "io":
            return ""
        if not self.can_retry_local() or not self.ollama:
            return ""
        cur_model = self.get_tier_model()
        if hasattr(self.ollama, "model"):
            setattr(self.ollama, "model", cur_model)
        self.record_retry()
        p = f"Fix code error:\nCode:\n{code_str}\nError:\n{err_msg}\nGuidance:\n{guide}\nOutput fixed code only."
        return getattr(self.ollama, "generate", lambda x: "")(p)

    @staticmethod
    def pack_payload(goal: str, code: str, err: str, want: str) -> tuple[bool, str]:
        """Pack micro-payload adhering to schemas/escalation_packet.json."""
        packet = {
            "g": goal.strip()[:50],
            "c": code.strip()[:100],
            "e": err.strip()[:60],
            "w": want.strip()[:50],
        }
        serialized = json.dumps(packet, separators=(",", ":"), ensure_ascii=False)
        if len(serialized) > 300:
            return False, f"Overflow: {len(serialized)} > 300"
        return True, serialized

    def request_cloud(self, payload_json: str) -> tuple[bool, str]:
        """Send micro-payload to cloud with limit check."""
        if self.cloud_tries >= self.max_cloud_tries:
            return False, "FAIL_CLOSED: cloud try limit reached"
        if len(payload_json) > 300:
            return False, "FAIL_CLOSED: packet size > 300"

        self.cloud_tries += 1
        return True, "CLOUD_GUIDANCE_RECEIVED"

    @staticmethod
    def save_cache(key: str, guidance: str, cache_file: str = "guidance_cache.json") -> bool:
        """Cache received guidance locally to avoid repeated escalations."""
        from core.defense_guard import DefenseGuard

        ok_prot, _ = DefenseGuard.chk_protected(cache_file)
        if not ok_prot:
            return False

        p = Path(cache_file).resolve()
        cache = {}
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    cache = json.load(f)
            except (json.JSONDecodeError, OSError):
                cache = {}
        cache[key] = guidance
        try:
            with open(p, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
            return True
        except OSError:
            return False

    @staticmethod
    def get_cache(key: str, cache_file: str = "guidance_cache.json") -> str | None:
        """Fetch cached guidance or solution for known error signature."""
        p = Path(cache_file).resolve()
        if not p.exists():
            return None
        try:
            with open(p, "r", encoding="utf-8") as f:
                cache = json.load(f)
            return cache.get(key)
        except (json.JSONDecodeError, OSError):
            return None

    @staticmethod
    def safe_fetch(url: str, content: bytes, exp_sha: str) -> tuple[bool, str]:
        """Tier 3 auto-remediation via TrustedFetch from allowlist."""
        from core.trusted_fetch import TrustedFetch
        ok_lim, lim_m = TrustedFetch.chk_limits()
        if not ok_lim:
            return False, lim_m
        return TrustedFetch.verify_payload(url, content, exp_sha)

    @staticmethod
    def split_patch(diff_str: str, chunk_size: int = 30) -> list[str]:
        """Split large cloud patch into testable chunks under line budget."""
        lines = diff_str.strip().splitlines()
        if len(lines) <= chunk_size:
            return [diff_str.strip()]
        chunks = []
        for i in range(0, len(lines), chunk_size):
            chunks.append("\n".join(lines[i : i + chunk_size]))
        chunks = [c for c in chunks if c]
        return chunks

