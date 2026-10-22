"""Tier 1 zero-cost deterministic fast router."""
import re
from typing import Dict, Optional

_PATTERNS = {
    "STATUS": re.compile(r"^\s*(status|статус|где мы|state)\s*$", re.I),
    "TEST": re.compile(r"^\s*(test|тест|run tests|прогони тесты)\s*$", re.I),
    "ABORT": re.compile(r"^\s*(abort|откат|rollback|cancel)\s*$", re.I),
    "VRAM": re.compile(r"^\s*(vram|память|gpu)\s*$", re.I),
}


class FastRouter:
    """Zero-token instant command classifier."""

    @staticmethod
    def match(text: str) -> Optional[Dict[str, str]]:
        """Match command in < 0.005s without models."""
        for intent, pattern in _PATTERNS.items():
            if pattern.match(text):
                return {"intent": intent, "cost": "0"}
        return None
