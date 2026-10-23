import hashlib
import os
from typing import Any, TypeVar

T = TypeVar("T")


def hash_file(path_str: str, chunk_size: int = 65536) -> str:
    """Calculate canonical SHA-256 hash of a file on disk."""
    if not verify_file(path_str):
        return ""
    hasher = hashlib.sha256()
    with open(path_str, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def hash_str(content: str) -> str:
    """Calculate canonical SHA-256 hash of in-memory text."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class FailClosedErr(Exception):
    """Raised when metric computation yields null or fails."""
    pass


def verify_file(path: str, min_sz: int = 1) -> bool:
    """Verify file exists, is regular file, and size >= min_sz."""
    if not os.path.exists(path):
        return False
    if not os.path.isfile(path):
        return False
    if os.path.getsize(path) < min_sz:
        return False
    return True


def check_metric(val: Any, name: str = "metric") -> Any:
    """Verify metric value strictly adheres to non-null invariant."""
    if val is None:
        raise FailClosedErr(f"Metric '{name}' returned null (Fail-Closed)")
    return val


def safe_calc(fn: Any, *args: Any, name: str = "calc", **kwargs: Any) -> dict:
    """Execute computation without validation theater, returning audit record."""
    try:
        res = fn(*args, **kwargs)
        if res is None:
            return {"name": name, "val": None, "ok": False, "err": "null_res"}
        return {"name": name, "val": res, "ok": True, "err": None}
    except Exception as exc:
        return {"name": name, "val": None, "ok": False, "err": str(exc)}


def run_fallback(primary_fn: Any, fallback_fn: Any, *args: Any, **kwargs: Any) -> Any:
    """Execute primary function, falling back to pure-Python on failure."""
    try:
        return primary_fn(*args, **kwargs)
    except Exception:
        return fallback_fn(*args, **kwargs)

