"""Safe fetch module for external trusted packages and code snippets."""

import hashlib
import time
import urllib.parse
from core.defense_guard import DefenseGuard


class TrustedFetch:
    """Zero-trust secure fetch gateway with strict allowlist and SHA-256."""

    ALLOW_HOSTS = ("raw.githubusercontent.com", "pypi.org")
    MAX_CODE_SIZE = 50 * 1024  # 50 KB
    MAX_PKG_SIZE = 5 * 1024 * 1024  # 5 MB
    MAX_PER_PLAN = 3
    MAX_PER_HOUR = 5

    _plan_count = 0
    _hour_history: list[float] = []

    @classmethod
    def reset_limits(cls) -> None:
        """Reset internal rate limiting counters for new plan/testing."""
        cls._plan_count = 0
        cls._hour_history.clear()

    @classmethod
    def chk_limits(cls) -> tuple[bool, str]:
        """Check session and hourly download quotas."""
        now = time.time()
        cls._hour_history = [t for t in cls._hour_history if now - t < 3600]
        if cls._plan_count >= cls.MAX_PER_PLAN:
            return False, "Quota: plan limit reached"
        if len(cls._hour_history) >= cls.MAX_PER_HOUR:
            return False, "Quota: hourly limit reached"
        return True, "OK"

    @classmethod
    def _chk_ast(cls, content: bytes) -> tuple[bool, str]:
        """Verify decoded Python code via DefenseGuard AST."""
        try:
            txt = content.decode("utf-8")
        except Exception as err:
            return False, f"Decode: {err}"
        ok_syn, s_msg = DefenseGuard.chk_syntax(txt)
        if not ok_syn:
            return False, f"AST syntax: {s_msg}"
        ok_id, i_msg = DefenseGuard.chk_ident(txt)
        if not ok_id:
            return False, f"AST ident: {i_msg}"
        ok_dan, d_msg = DefenseGuard.chk_danger(txt)
        if not ok_dan:
            return False, f"AST danger: {d_msg}"
        return True, "OK"

    @classmethod
    def verify_payload(
        cls, url: str, content: bytes, exp_sha: str
    ) -> tuple[bool, str]:
        """Validate source URL, content size, SHA-256 and AST safety."""
        try:
            host = urllib.parse.urlparse(url).netloc.lower()
        except Exception:
            return False, "ESCAPE_ATTEMPT: bad URL"

        if host not in cls.ALLOW_HOSTS:
            return False, f"ESCAPE_ATTEMPT: host '{host}' not in allowlist"

        is_pkg = url.endswith(".whl") or url.endswith(".tar.gz")
        max_sz = cls.MAX_PKG_SIZE if is_pkg else cls.MAX_CODE_SIZE
        if len(content) > max_sz:
            return False, f"Size {len(content)} > limit {max_sz}"

        act_sha = hashlib.sha256(content).hexdigest().lower()
        if act_sha != exp_sha.lower():
            return False, f"Hash mismatch: expected {exp_sha}, got {act_sha}"

        if not is_pkg:
            ok_ast, ast_msg = cls._chk_ast(content)
            if not ok_ast:
                return False, ast_msg

        cls._plan_count += 1
        cls._hour_history.append(time.time())
        return True, "OK"
