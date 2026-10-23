"""Semantic golden template memory with Fail-Closed integrity guard."""

import ast
import hashlib
import json
import os
from pathlib import Path
from typing import Optional


from core.artifact_guard import hash_str


class SemanticMemory:
    """Store and retrieve golden code templates with integrity validation."""

    def __init__(self, root: str = "memory/templates") -> None:
        """Initialize semantic template store."""
        self.root = root

    @staticmethod
    def calc_hash(content: str) -> str:
        """Calculate canonical SHA-256 checksum."""
        return hash_str(content)

    def _get_path(self, cat: str, key: str) -> str:
        """Construct deterministic file path strictly within root sandbox."""
        from pathlib import Path
        root_p = Path(self.root).resolve()
        target_p = (root_p / cat / f"{key}.json").resolve()
        if not target_p.is_relative_to(root_p):
            raise ValueError(f"Sandbox escape detected: {cat}/{key}")
        return str(target_p)

    def save_tmpl(self, cat: str, key: str, code: str) -> bool:
        """Save template with SHA-256, AST syntax and danger validation (Fail-Closed)."""
        if not isinstance(code, str):
            return False
        try:
            ast.parse(code)
            from core.defense_guard import DefenseGuard
            is_safe, _ = DefenseGuard.chk_danger(code)
            if not is_safe:
                return False

            h_val = self.calc_hash(code)
            path = self._get_path(cat, key)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            rec = {
                "cat": cat,
                "key": key,
                "code": code,
                "sha256": h_val,
                "ver": 1,
            }
            temp_path = Path(path).with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(rec, f, indent=2, ensure_ascii=False)
            temp_path.replace(path)
            return True
        except (SyntaxError, ValueError, OSError, TypeError):
            # AUD-FITE-009 & AUD-FITE-017: Fail-closed on sandbox escape and type/IO errors
            return False

    def get_tmpl(self, cat: str, key: str) -> Optional[str]:
        """Load template with strict integrity and AST check (Fail-Closed)."""
        try:
            path = self._get_path(cat, key)
        except (ValueError, OSError, TypeError):
            # AUD-FITE-029: Fail-closed sandbox escape on get_tmpl
            return None
        if not path or not os.path.isfile(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                rec = json.load(f)
            code = rec.get("code", "")
            saved_h = rec.get("sha256", "")
            if not code or not saved_h or self.calc_hash(code) != saved_h:
                return None
            ast.parse(code)
            return str(code)
        except Exception:
            return None
