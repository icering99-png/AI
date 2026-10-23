"""Deterministic Tier 0 defense guard."""

import ast
from pathlib import Path
import re
import unicodedata

_APPROVE_TOKEN_RE = re.compile(r"^APPROVE\s+([A-Za-z0-9_\-]+)$")
_ENC_RE = re.compile(
    r"(?i)(?:[-/](?:encodedcommand|encoded|enco|enc)\b|\b(?:powershell|pwsh)\b.*[-/](?:e|enc|encodedcommand)\b|\bfrombase64string\b)"
)
_NET_CMD_RE = re.compile(
    r"(?i)\b(?:curl|wget|iwr|irm|invoke-webrequest|invoke-restmethod|certutil|bitsadmin)\b"
)
_NET_LIB_RE = re.compile(
    r"(?i)\b(?:webclient|httpclient|system\.net|urllib|requests|httpx|aiohttp|fetch|axios)\b"
)
_REC_LIST_RE = re.compile(
    r"(?i)(?:\b(?:get-childitem|gci)\b.*-(?:recurse|r)\b|\bdir\b.*/s\b|\bls\b.*-r\b|\bfind\b\s+[^|\n]+$)"
)
_GC_RE = re.compile(r"(?i)\b(?:get-content|gc)\b")
_GC_LIMIT_RE = re.compile(
    r"(?i)-(?:totalcount|head|tail|first|last)\b|\b(?:select-object|select)\b.*-(?:first|last)\b"
)
_CAT_DUMP_RE = re.compile(r"(?i)^\s*(?:cat|type)\s+[^|><\n]+$")


def is_valid_token(token: str, expected_plan: str | None = None) -> bool:
    """Validate approval token structure and optional plan ID binding."""
    if not isinstance(token, str):
        return False
    match = _APPROVE_TOKEN_RE.fullmatch(token.strip())
    if not match:
        return False
    if expected_plan is not None:
        if not isinstance(expected_plan, str):
            return False
        return match.group(1) == expected_plan.strip()
    return True


class DefenseGuard:
    """TIER_0 deterministic AST and sandbox guard."""

    def __init__(self) -> None:
        """Initialize guard and run self-test."""
        if not self.self_test():
            raise RuntimeError("DefenseGuard canary self-test failed")

    @classmethod
    def self_test(cls) -> bool:
        """Run canary self-test on known good and bad snippets."""
        good = "def run_ok(val: int) -> int:\n    return val + 1"
        bad = "def fail_func():\n    eval('1+1')"
        ok_syn, _ = cls.chk_syntax(good)
        ok_id, _ = cls.chk_ident(good)
        ok_dan, _ = cls.chk_danger(good)
        if not (ok_syn and ok_id and ok_dan):
            return False
        bad_dan, _ = cls.chk_danger(bad)
        if bad_dan:
            return False
        return True

    @staticmethod
    def chk_syntax(code: str) -> tuple[bool, str]:
        """Verify Python syntax via AST safely (AUD-FITE-038)."""
        if not isinstance(code, str):
            return False, "Invalid code type: expected str"
        try:
            ast.parse(code)
            return True, "OK"
        except (SyntaxError, TypeError) as err:
            return False, f"Syntax: {err}"

    @staticmethod
    def get_defs(code: str) -> list[tuple[str, str]]:
        """Extract top-level definitions as (name, 'function'|'class')."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        defs = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defs.append((node.name, "function"))
            elif isinstance(node, ast.ClassDef):
                defs.append((node.name, "class"))
        return defs

    @staticmethod
    def chk_ident(code: str, limit: int = 15) -> tuple[bool, str]:
        """Verify identifier names length limit safely (AUD-FITE-038)."""
        if not isinstance(code, str):
            return False, "Invalid code type: expected str"
        try:
            tree = ast.parse(code)
        except (SyntaxError, TypeError):
            return False, "Syntax error"

        for node in ast.walk(tree):
            name = ""
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = node.name
            elif isinstance(node, ast.arg):
                name = node.arg
            elif isinstance(node, ast.Name):
                name = node.id

            if not name:
                continue
            if name.startswith("__") and name.endswith("__"):
                continue
            if len(name) > limit:
                return False, f"Ident '{name}' > {limit}"
        return True, "OK"

    @staticmethod
    def chk_path(path_str: str, root_str: str) -> tuple[bool, str]:
        """Verify path liveness and sandbox boundary safely (AUD-FITE-041)."""
        try:
            root_p = Path(root_str).resolve()
            target_p = Path(path_str).resolve()
        except (ValueError, RuntimeError, TypeError) as err:
            return False, f"Invalid path: {err}"

        if not target_p.is_relative_to(root_p):
            return False, f"Escape: {path_str}"
        if not target_p.exists():
            return False, f"Not found: {path_str}"
        return True, "OK"

    IMMUTABLE_LOGS = ("logs", "guard_audit.jsonl")
    PROTECTED_ROOTS = ("tests", "schemas", "rules", "knowledgebase", ".agents", "logs")
    PROTECTED_FILES = ("agents.md", "coding_standards.md", "failure_index.json", "hooks.json", "guard_audit.jsonl")

    @classmethod
    def chk_protected(
        cls,
        path_str: str,
        allow_test_edit: bool = False,
        approve_token: str = "",
        expected_plan: str | None = None,
    ) -> tuple[bool, str]:
        """Verify file path is not a protected rule, contract, or audit log."""
        if not isinstance(path_str, str) or not path_str.strip():
            return False, "PROTECTED_PATH_VIOLATION: Invalid path type"
        clean = path_str.replace("\\", "/").strip()
        while clean.startswith("./"):
            clean = clean[2:]
        norm_parts = [unicodedata.normalize("NFC", p).lower() for p in clean.split("/") if p and p != "."]

        # AUD-FITE-027: Scoped match: roots match top-level component, files match basename
        is_root_hit = bool(norm_parts and norm_parts[0] in cls.PROTECTED_ROOTS)
        is_file_hit = bool(norm_parts and norm_parts[-1] in cls.PROTECTED_FILES)
        hit_protected = [norm_parts[0]] if is_root_hit else ([norm_parts[-1]] if is_file_hit else [])
        if not hit_protected:
            return True, "OK"

        # AUD-020 & AUD-FITE-039: Logs immutable at root or guard_audit.jsonl, allows tests/logs/ with token
        if norm_parts and norm_parts[0] == "logs":
            return False, f"PROTECTED_PATH_VIOLATION: {path_str}"
        if norm_parts and norm_parts[-1] == "guard_audit.jsonl":
            return False, f"PROTECTED_PATH_VIOLATION: {path_str}"

        # AUD-FITE-006: Tests, schemas, rules and AGENTS.md allowed strictly with valid token
        if allow_test_edit and is_valid_token(approve_token, expected_plan):
            return True, "OK"

        return False, f"PROTECTED_PATH_VIOLATION: {path_str}"

    @staticmethod
    def chk_diff(diff_txt: str, max_l: int = 30) -> tuple[bool, str]:
        """Verify diff change line count limit."""
        cnt = 0
        for line in diff_txt.splitlines():
            s = line.strip()
            is_diff_hdr = (s.startswith("+++ b/") or s.startswith("+++ a/") or 
                           s.startswith("--- a/") or s.startswith("--- b/") or
                           s == "+++" or s == "---")
            if not s or is_diff_hdr:
                continue
            if s.startswith("+") or s.startswith("-"):
                cnt += 1
        if cnt > max_l:
            return False, f"Diff {cnt} > {max_l}"
        return True, "OK"

    @staticmethod
    def chk_danger(code: str) -> tuple[bool, str]:
        """Detect forbidden dynamic or destructive calls safely (AUD-FITE-038)."""
        if not isinstance(code, str):
            return False, "Invalid code type: expected str"
        try:
            tree = ast.parse(code)
        except (SyntaxError, TypeError):
            return False, "Syntax error"

        banned_calls = {"eval", "exec", "__import__", "getattr", "vars"}
        banned_roots = {"__builtins__", "builtins", "importlib"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in banned_roots:
                return False, f"Banned: {node.id}"
            if isinstance(node, ast.Attribute) and node.attr in banned_calls:
                return False, f"Banned: {node.attr}"
            if isinstance(node, ast.Call):
                name = ""
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    name = node.func.attr
                if name in banned_calls:
                    return False, f"Banned: {name}"
        return True, "OK"

    @classmethod
    def _chk_enc(cls, cmd: str) -> tuple[bool, str]:
        """Detect encoded commands."""
        if _ENC_RE.search(cmd):
            return False, "BANNED_ENCODED_COMMAND"
        return True, "OK"

    @classmethod
    def _chk_net(cls, cmd: str) -> tuple[bool, str]:
        """Detect network fetch tools, aliases, and direct API libraries."""
        norm = re.sub(r"[`\"'\^]", "", cmd)
        if _NET_CMD_RE.search(norm):
            return False, "BANNED_NETWORK_TOOL"
        if _NET_LIB_RE.search(norm):
            return False, "BANNED_NETWORK_API"
        return True, "OK"

    @classmethod
    def _chk_dump(cls, cmd: str) -> tuple[bool, str]:
        """Enforce 'Do not dump - derive' principle."""
        if _REC_LIST_RE.search(cmd):
            return False, "UNCONSTRAINED_RECURSIVE_LISTING"
        if _GC_RE.search(cmd) and not _GC_LIMIT_RE.search(cmd):
            return False, "UNCONSTRAINED_GET_CONTENT"
        if _CAT_DUMP_RE.search(cmd.strip()):
            return False, "UNCONSTRAINED_FILE_DUMP"
        return True, "OK"

    @classmethod
    def chk_cmd(cls, cmd: str) -> tuple[bool, str]:
        """Check command against encoded, network and flood dumping vectors."""
        if not isinstance(cmd, str) or not cmd.strip():
            return False, "EMPTY_COMMAND"
        ok_enc, enc_msg = cls._chk_enc(cmd)
        if not ok_enc:
            return False, enc_msg
        ok_net, net_msg = cls._chk_net(cmd)
        if not ok_net:
            return False, net_msg
        ok_dmp, dmp_msg = cls._chk_dump(cmd)
        if not ok_dmp:
            return False, dmp_msg
        return True, "PASS"

