import re
from datetime import timedelta

DURATION_RE = re.compile(r"(\d+)(s|m|h|d)")

SECONDS_MAP = {"s": 1, "m": 60, "h": 3600, "d": 86400}

def parse_duration(s: str) -> timedelta | None:
    match = DURATION_RE.fullmatch(s.lower().strip())
    if not match:
        return None
    value, unit = int(match.group(1)), match.group(2)
    return timedelta(seconds=value * SECONDS_MAP[unit])

def parse_duration_with_label(s: str) -> tuple[int, str] | None:
    match = DURATION_RE.fullmatch(s.lower().strip())
    if not match:
        return None
    value, unit = int(match.group(1)), match.group(2)
    return value * SECONDS_MAP[unit], f"{value}{unit}"