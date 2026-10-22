"""Regression & Backward Compatibility Guard."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path


from core.artifact_guard import hash_file


class RegressGuard:
    """Guard against regressions and unauthorized file drift."""

    @staticmethod
    def hash_file(path_str: str) -> str:
        """Calculate canonical SHA-256 hash safely, supporting 0-byte files (AUD-FITE-040)."""
        try:
            p = Path(path_str).resolve()
            if not p.is_file():
                return ""
            hasher = hashlib.sha256()
            with open(p, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except OSError:
            return ""

    @staticmethod
    def save_manifest(files: list[str], out_path: str) -> bool:
        """Create or update state manifest with SHA-256 hashes deterministically."""
        if not isinstance(files, (list, tuple, set)):
            return False
        manifest = {}
        try:
            for f in files:
                p = Path(f).resolve()
                if p.exists() and p.is_file():
                    manifest[p.as_posix()] = RegressGuard.hash_file(str(p))

            out_p = Path(out_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            temp_out = out_p.with_suffix(".tmp")
            with open(temp_out, "w", encoding="utf-8") as out:
                json.dump(manifest, out, indent=2, sort_keys=True, ensure_ascii=False)
            temp_out.replace(out_p)
            return True
        except Exception:
            return False

    @staticmethod
    def chk_manifest(manifest_path: str) -> tuple[bool, list[str]]:
        """Verify files against recorded SHA-256 hashes, detecting drift and deletions (AUD-FITE-040)."""
        try:
            p = Path(manifest_path).resolve()
            if not p.exists():
                return True, []
            with open(p, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            if not isinstance(manifest, dict):
                return False, ["Corrupt manifest"]
            drifted = []
            for file_p, expected_hash in manifest.items():
                if not Path(file_p).is_file():
                    drifted.append(file_p)
                    continue
                current_hash = RegressGuard.hash_file(file_p)
                if current_hash != expected_hash:
                    drifted.append(file_p)
            return len(drifted) == 0, drifted
        except (json.JSONDecodeError, OSError):
            return False, ["Corrupt manifest"]

    @staticmethod
    def run_golden(golden_dir: str = "tests/golden") -> tuple[bool, str]:
        """Execute all golden test invariants in external process."""
        p = Path(golden_dir).resolve()
        if not p.exists():
            return True, "No golden tests dir"

        cmd = [sys.executable, "-m", "unittest", "discover", "-s", str(p)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            return False, f"Golden failed: {res.stderr or res.stdout}"
        return True, "Golden PASS"
