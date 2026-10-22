# core/ste_guard.py
"""Procedural step validator for ASD-STE100 with REVIEW fallback."""
from __future__ import annotations
import re


class SteGuard:
    """Validates procedural instructions for word limits with ambiguity handling."""

    @classmethod
    def check_step(cls, text: str) -> dict[str, str | int | bool]:
        """Verify procedural step is <= 20 words or yield REVIEW if ambiguous."""
        clean = text.strip()
        if not clean:
            return {"status": "PASS", "words": 0, "ok": True}

        # Check for ambiguity indicators: ellipses or mismatched punctuation
        if "..." in clean or clean.count("(") != clean.count(")"):
            return {"status": "REVIEW", "words": 0, "ok": False, "reason": "Ambiguous syntax"}

        # Mask code tokens, URLs and paths to single semantic tokens
        masked = re.sub(r"`[^`]+`", "__CODE__", clean)
        masked = re.sub(r"https?://\S+", "__URL__", masked)
        masked = re.sub(r"[\w.-]+[/\\][\w.-]+", "__PATH__", masked)

        words = [w for w in re.split(r"\s+", masked.strip()) if w]
        count = len(words)

        if count > 20:
            return {"status": "FAIL", "words": count, "ok": False, "reason": "Exceeds 20 words"}

        return {"status": "PASS", "words": count, "ok": True}
