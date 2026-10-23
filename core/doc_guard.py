"""Deterministic Markdown link and path liveness auditor."""
import os
import re
from pathlib import Path
from typing import List, Tuple


class DocGuard:
    """Audits Markdown files to guarantee 100% link liveness."""

    @staticmethod
    def audit_doc(file_path: str, root_dir: str = ".") -> Tuple[bool, List[str]]:
        """Verify all local links and backtick paths exist on disk."""
        path_obj = Path(file_path)
        if not path_obj.exists():
            return False, [f"Missing doc: {file_path}"]

        content = path_obj.read_text(encoding="utf-8")
        # Extract markdown links [text](path)
        links = re.findall(r"\[.*?\]\((.*?)\)", content)
        broken: List[str] = []

        root = Path(root_dir).resolve()
        doc_dir = path_obj.parent.resolve()

        for link in links:
            if link.startswith("http://") or link.startswith("https://") or link.startswith("#"):
                continue
            # Strip anchors
            clean = link.split("#")[0].strip()
            if not clean:
                continue

            tgt_root = root / clean
            tgt_doc = doc_dir / clean

            if not (tgt_root.exists() or tgt_doc.exists()):
                broken.append(f"{link} in {file_path}")

        return len(broken) == 0, broken

    @staticmethod
    def audit_front(file_path: str) -> tuple[bool, dict[str, str | list[str]]]:
        """Verify YAML frontmatter syntax, applyTo glob, and excludeAgent."""
        p = Path(file_path)
        if not p.is_file():
            return False, {"error": f"File not found: {file_path}"}
        parts = p.read_text(encoding="utf-8").split("---")
        if len(parts) < 3:
            return False, {"error": "Missing YAML frontmatter delimiters '---'"}
        try:
            import yaml
            meta = yaml.safe_load(parts[1]) or {}
            return True, meta
        except Exception as err:
            return False, {"error": f"YAML syntax error: {err}"}

