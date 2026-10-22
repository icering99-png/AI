"""Automated, tamper-evident audit logger for pipeline operations."""

import json
import time
from pathlib import Path
from core.artifact_guard import hash_str


class AuditLogger:
    """Enforces programmatic logging into logs/guard_audit.jsonl."""

    REQUIRED_KEYS = ("timestamp", "step", "target", "status", "prev_hash", "entry_hash")

    def __init__(self, log_path: str = "logs/guard_audit.jsonl"):
        self.log_path = Path(log_path).resolve()
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def _calc_hash(self, ts: float, step: str, target: str, status: str, prev_hash: str = "GENESIS") -> str:
        """Deterministic hash combining entry payload and previous entry hash."""
        payload = f"{ts:.6f}:{step}:{target}:{status}:{prev_hash}"
        return hash_str(payload)[:32]

    def _get_last_hash(self) -> str:
        """Fetch hash of the last entry in the log to maintain chain integrity."""
        if not self.log_path.exists():
            return "GENESIS"
        lines = [line.strip() for line in self.log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not lines:
            return "GENESIS"
        try:
            return json.loads(lines[-1]).get("entry_hash", "GENESIS")
        except Exception:
            return "GENESIS"

    def log(
        self,
        step: str,
        target: str,
        status: str,
        details: dict | None = None,
    ) -> dict:
        """Write automated append-only record with programmatic timestamp and hash chain."""
        ts = time.time()
        prev_h = self._get_last_hash()
        entry_hash = self._calc_hash(ts, step, target, status, prev_h)
        rec = {
            "timestamp": ts,
            "step": step,
            "target": target,
            "status": status,
            "prev_hash": prev_h,
            "entry_hash": entry_hash,
        }
        if details:
            rec.update(details)

        line = json.dumps(rec, ensure_ascii=False)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        return rec

    def verify_log(self) -> tuple[bool, str]:
        """Audit existing log file for schema compliance, hash validity, and chain unbrokenness."""
        if not self.log_path.exists():
            return True, "EMPTY_LOG"

        lines = self.log_path.read_text(encoding="utf-8").strip().splitlines()
        expected_prev = "GENESIS"
        for idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as err:
                return False, f"TAMPERED_OR_INVALID_SCHEMA: Line {idx+1} invalid JSON: {err}"

            for key in self.REQUIRED_KEYS:
                if key not in data:
                    return False, f"TAMPERED_OR_INVALID_SCHEMA: Line {idx+1} missing '{key}'"

            if data.get("prev_hash") != expected_prev:
                return False, f"TAMPERED_OR_INVALID_SCHEMA: Line {idx+1} chain broken (deletion detected)"

            expected = self._calc_hash(
                data["timestamp"], data["step"], data["target"], data["status"], expected_prev
            )
            if data["entry_hash"] != expected:
                return False, f"TAMPERED_OR_INVALID_SCHEMA: Line {idx+1} hash mismatch"
            expected_prev = data["entry_hash"]

        return True, "VALID"
