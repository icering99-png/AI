"""Runbook and deployment specification generator with integrity guards."""

import ast
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


from core.artifact_guard import hash_file


class RunbookGen:
    """Generate and verify machine-readable deployment runbooks."""

    @staticmethod
    def calc_sha(path: str) -> str:
        """Calculate canonical SHA-256 hash of a file."""
        return hash_file(path, chunk_size=65536)

    @staticmethod
    def chk_entry(path: str, name: str) -> Tuple[bool, Optional[str]]:
        """Verify entry point in file AST using canonical DefenseGuard."""
        if not os.path.isfile(path):
            return False, None
        try:
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
        except Exception:
            return False, None

        from core.defense_guard import DefenseGuard

        for def_name, def_kind in DefenseGuard.get_defs(code):
            if def_name == name:
                return True, def_kind
        return False, None

    def gen_spec(
        self,
        mod: str,
        files: List[str],
        entry: str = "main",
        envs: Optional[List[str]] = None,
        cmd: str = "run",
        out_p: str = "runbook.json",
        sem_key: Optional[str] = None,
        kind: str = "python",
    ) -> Dict[str, Any]:
        """Generate verified deployment runbook atomically with SHA-256 state (AUD-FITE-042)."""
        if not isinstance(files, (list, tuple)) or not isinstance(out_p, (str, Path)) or not files or not entry:
            return {"ok": False, "err": "empty_input", "reason": "invalid_types"}

        for p in files:
            if not isinstance(p, (str, Path)) or not os.path.isfile(p):
                return {"ok": False, "err": f"missing_file: {p}", "reason": "file_missing"}

        has_entry, def_kind = self.chk_entry(str(files[0]), entry)
        if not has_entry:
            if entry != "main":
                return {"ok": False, "err": f"entry_missing: {entry}", "reason": f"entry_missing: {entry}"}
            effective_kind = kind
        else:
            effective_kind = def_kind

        arts = []
        for p in files:
            arts.append(
                {"path": str(p), "sha256": self.calc_sha(str(p)), "size": os.path.getsize(p)}
            )

        spec = {
            "mod": mod,
            "artifacts": arts,
            "entry": entry,
            "kind": effective_kind,
            "envs": envs if envs is not None else [],
            "cmd": cmd,
            "sem_key": sem_key or "",
            "status": "VERIFIED",
        }
        try:
            out_path = Path(out_p).resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            temp_p = out_path.with_suffix(".tmp")
            with open(temp_p, "w", encoding="utf-8") as f:
                json.dump(spec, f, indent=2, ensure_ascii=False)
            temp_p.replace(out_path)
            return {"ok": True, "spec": spec}
        except Exception as err:
            return {"ok": False, "err": str(err), "reason": str(err)}

    def verify_spec(self, spec_p: str) -> Dict[str, Any]:
        """Verify runbook artifacts integrity."""
        if not os.path.isfile(spec_p):
            return {"ok": False, "reason": "spec_missing"}
        try:
            with open(spec_p, "r", encoding="utf-8") as f:
                spec = json.load(f)
        except Exception:
            return {"ok": False, "reason": "invalid_json"}

        arts = spec.get("artifacts", [])
        if not arts:
            return {"ok": False, "reason": "empty_artifacts"}

        for art in arts:
            p = art.get("path", "")
            if not os.path.isfile(p):
                return {"ok": False, "reason": "file_missing"}
            if self.calc_sha(p) != art.get("sha256", ""):
                return {"ok": False, "reason": "hash_mismatch"}

        return {"ok": True, "reason": "ok"}

    def update_spec(
        self,
        spec_p: str,
        approve_token: str = "",
        expected_plan: str | None = None,
    ) -> bool:
        """Update artifact hashes strictly upon valid authorization token (AUD-FITE-037)."""
        from core.defense_guard import is_valid_token

        if not is_valid_token(approve_token, expected_plan):
            return False
        if not isinstance(spec_p, (str, Path)):
            return False
        try:
            if not os.path.isfile(spec_p):
                return False
            with open(spec_p, "r", encoding="utf-8") as f:
                spec = json.load(f)
            if not isinstance(spec, dict) or not isinstance(spec.get("artifacts"), list):
                return False
            for art in spec["artifacts"]:
                if not isinstance(art, dict):
                    return False
                p = art.get("path", "")
                if not isinstance(p, (str, Path)) or not os.path.isfile(p):
                    return False
                art["sha256"] = self.calc_sha(str(p))
                art["size"] = os.path.getsize(p)
            spec["status"] = "VERIFIED"
            temp_p = Path(spec_p).with_suffix(".tmp")
            with open(temp_p, "w", encoding="utf-8") as f:
                json.dump(spec, f, indent=2, ensure_ascii=False)
            temp_p.replace(spec_p)
            return True
        except Exception:
            return False
