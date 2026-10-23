import hashlib
import json
import os
import re
import subprocess
from pathlib import Path


class BranchGuard:
    """Manages hypothesis scratch branches and failure logging."""

    @staticmethod
    def _run_git(args: list[str], timeout_sec: int = 10) -> tuple[int, str]:
        """Execute git command safely with timeout ceiling and terminal prompt disabled."""
        if not isinstance(args, list) or not all(isinstance(x, str) for x in args):
            return 1, "Invalid args"
        env = dict(os.environ)
        env["GIT_TERMINAL_PROMPT"] = "0"
        try:
            res = subprocess.run(
                ["git"] + args,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_sec,
                env=env,
            )
            out = res.stdout.strip()
            err = res.stderr.strip()
            msg = out if res.returncode == 0 else (err or out)
            return res.returncode, msg
        except subprocess.TimeoutExpired:
            return 1, f"TIMEOUT: Git command timed out after {timeout_sec}s"
        except OSError as err:
            return 1, str(err)

    @classmethod
    def create_hypo(cls, name: str) -> tuple[bool, str]:
        """Create and checkout temporary hypothesis scratch branch."""
        bname = f"scratch/hypo-{name.strip()[:10]}"
        code, out = cls._run_git(["checkout", "-b", bname])
        return (code == 0), out or bname

    @classmethod
    def abort_hypo(
        cls,
        name: str,
        reason: str,
        main_br: str = "main",
        fail_path: str = "failure_index.json",
    ) -> bool:
        """Abort hypothesis, checkout main and record into failure index safely."""
        from datetime import date
        if not isinstance(name, str) or not name.strip():
            return False
        clean_name = re.sub(r"[^A-Za-z0-9_\-]", "", name.strip())[:10]
        if not clean_name:
            return False

        # AUD-FITE-021: Fail-closed type safety on reason
        safe_reason = reason.strip()[:100] if isinstance(reason, str) else str(reason)[:100]

        p = Path(fail_path).resolve()
        data = {"failures": []}
        # AUD-FITE-007: Safe handling of empty/new files vs existing failure registry
        if p.exists() and p.stat().st_size > 0:
            try:
                with open(p, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if not isinstance(loaded, dict) or "failures" not in loaded or not isinstance(loaded["failures"], list):
                    return False
                data = loaded
            except (json.JSONDecodeError, OSError):
                return False

        # AUD-FITE-022, AUD-FITE-034: Hash suffix on name and reason prevents collisions
        h_suffix = hashlib.sha256(f"{name}:{safe_reason}".encode("utf-8")).hexdigest()[:4].upper()
        base_id = f"FAIL-{clean_name[:6].upper()}-{h_suffix}"
        # AUD-FITE-036: Filter existing_ids strictly to strings
        existing_ids = {
            f.get("id")
            for f in data["failures"]
            if isinstance(f, dict) and isinstance(f.get("id"), str)
        }
        cand_id = base_id
        counter = 1
        while cand_id in existing_ids:
            cand_id = f"{base_id[:16]}-{counter}"
            counter += 1

        item = {
            "id": cand_id,
            "symptom": f"Hypothesis {name.strip()} rejected",
            "root_cause": safe_reason,
            "prohibition": f"Avoid {clean_name} approach",
            "date": date.today().isoformat(),  # AUD-FITE-012: dynamic ISO date
            "status": "DISPROVEN",
        }
        data["failures"].append(item)

        try:
            temp_p = p.with_suffix(".tmp")
            with open(temp_p, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            temp_p.replace(p)
        except OSError:
            return False

        bname = f"scratch/hypo-{clean_name}"
        # AUD-FITE-023: Check returncode of git checkout to prevent fail-open
        code_co, out_co = cls._run_git(["checkout", "-f", main_br])
        if code_co != 0 and any(s in out_co.lower() for s in ("already on", "did not match any file", "your current branch")):
            code_co = 0
        if code_co != 0:
            return False
        # AUD-FITE-035: Verify scratch branch deletion returncode
        code_del, out_del = cls._run_git(["branch", "-D", bname])
        if code_del != 0 and "not found" not in out_del.lower() and "did not match any file" not in out_del.lower():
            return False
        return True
