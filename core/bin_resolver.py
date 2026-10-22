"""Cross-platform deterministic binary resolver."""

import os
import shutil
from typing import Optional, Sequence


def resolve_bin(name: str, roots: Optional[Sequence[str]] = None) -> Optional[str]:
    """Resolve binary in PATH and standard Windows prefixes."""
    found = shutil.which(name) or shutil.which(f"{name}.exe")
    if found:
        return str(found)

    dirs = [
        os.environ.get("ProgramFiles", r"C:\Program Files"),
        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
        os.environ.get("LOCALAPPDATA", ""),
        os.environ.get("SystemRoot", r"C:\Windows") + r"\System32",
    ]
    if roots:
        dirs.extend(roots)

    for prefix in dirs:
        if not prefix:
            continue
        cand = os.path.join(prefix, name, f"{name}.exe")
        if os.path.isfile(cand):
            return str(cand)
        cand_dir = os.path.join(prefix, f"{name}.exe")
        if os.path.isfile(cand_dir):
            return str(cand_dir)

    return None
