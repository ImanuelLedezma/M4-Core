"""Verify time_utils parses all valid duration formats correctly
and rejects invalid input — prevents silent cooldown bypass."""
from helpers.time_utils import parse_duration, parse_duration_with_label


def verify_seconds():
    result = parse_duration("30s")
    assert result is not None, "30s should parse"
    assert result.total_seconds() == 30, "30s should be 30 seconds"


def verify_minutes():
    result = parse_duration("5m")
    assert result is not None, "5m should parse"
    assert result.total_seconds() == 300, "5m should be 300 seconds"


def verify_hours():
    result = parse_duration("2h")
    assert result is not None, "2h should parse"
    assert result.total_seconds() == 7200, "2h should be 7200 seconds"


def verify_days():
    result = parse_duration("1d")
    assert result is not None, "1d should parse"
    assert result.total_seconds() == 86400, "1d should be 86400 seconds"


def verify_invalid_rejected():
    assert parse_duration("abc") is None, "abc should be rejected"
    assert parse_duration("") is None, "empty string should be rejected"
    assert parse_duration("5x") is None, "5x should be rejected"


def verify_label_extraction():
    result = parse_duration_with_label("10m")
    assert result is not None
    seconds, label = result
    assert seconds == 600, "10m label should be 600s"
    assert label == "10m", "label should be '10m'"


def verify_case_insensitive():
    result = parse_duration("5M")
    assert result is not None, "5M should parse"
    assert result.total_seconds() == 300, "5M should be 300 seconds"


def verify_whitespace_tolerance():
    result = parse_duration("  5m  ")
    assert result is not None, "whitespace should be stripped"
    assert result.total_seconds() == 300


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("verify_") and callable(fn):
            fn()
            print(f"  [OK] {name.replace('verify_', '').replace('_', ' ')}")
