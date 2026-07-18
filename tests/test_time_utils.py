"""Tests for helpers/time_utils.py"""
from helpers.time_utils import parse_duration, parse_duration_with_label


def test_parse_duration_seconds():
    result = parse_duration("30s")
    assert result is not None
    assert result.total_seconds() == 30


def test_parse_duration_minutes():
    result = parse_duration("5m")
    assert result is not None
    assert result.total_seconds() == 300


def test_parse_duration_hours():
    result = parse_duration("2h")
    assert result is not None
    assert result.total_seconds() == 7200


def test_parse_duration_days():
    result = parse_duration("1d")
    assert result is not None
    assert result.total_seconds() == 86400


def test_parse_duration_invalid():
    assert parse_duration("abc") is None
    assert parse_duration("") is None
    assert parse_duration("5x") is None


def test_parse_duration_with_label():
    result = parse_duration_with_label("10m")
    assert result is not None
    seconds, label = result
    assert seconds == 600
    assert label == "10m"


def test_parse_duration_case_insensitive():
    result = parse_duration("5M")
    assert result is not None
    assert result.total_seconds() == 300


def test_parse_duration_whitespace():
    result = parse_duration("  5m  ")
    assert result is not None
    assert result.total_seconds() == 300
