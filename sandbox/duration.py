import re

UNIT_MULTIPLIERS = {
    "h": 3600,
    "m": 60,
    "s": 1,
}

TOKEN_PATTERN = re.compile(r"^(\d+)([hms])$")

def parse_duration(value: str) -> int:
    if not isinstance(value, str):
        raise TypeError(f"Expected str, got {type(value).__name__}")

    stripped = value.strip()
    if not stripped:
        raise ValueError("Empty duration string")

    tokens = stripped.split()
    total_seconds = 0
    seen_units: set[str] = set()

    for token in tokens:
        match = TOKEN_PATTERN.match(token)
        if not match:
            raise ValueError(f"Invalid duration token: {token!r}")
        amount_str, unit = match.groups()
        if unit in seen_units:
            raise ValueError(f"Repeated duration unit: {unit!r}")
        seen_units.add(unit)
        total_seconds += int(amount_str) * UNIT_MULTIPLIERS[unit]

    return total_seconds
