"""Data integrity sanity checks run at startup.

Validates SQLite database, config, and admin files for corruption
or missing data that would cause runtime failures.
"""
import os
import sys
import math

DATA_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))
CONFIG_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.yaml"))
ADMINS_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "admins.yaml"))
REQUIRED_CHANNEL_KEYS = ("log", "console", "ai_chat", "dictionary", "confession", "hall_of_fame", "welcome")

_errors: list[str] = []
_warnings: list[str] = []


def check_data_directory():
    if not os.path.isdir(DATA_DIR):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            _warnings.append(f"created missing data directory at {DATA_DIR}")
        except OSError as e:
            _errors.append(f"cannot create data directory {DATA_DIR}: {e}")


def check_bank_integrity():
    from helpers.database import bank_all
    try:
        bank = bank_all()
    except Exception as e:
        _errors.append(f"bank database error: {e}")
        return
    for uid, acct in bank.items():
        for field in ("wallet", "bank", "debt"):
            val = acct.get(field)
            if val is None:
                _errors.append(f"bank: account '{uid}' missing '{field}'")
            elif not isinstance(val, (int, float)):
                _errors.append(f"bank: account '{uid}' '{field}' is not a number (got {type(val).__name__})")
            elif isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                _errors.append(f"bank: account '{uid}' '{field}' is NaN/inf")
            elif val < 0:
                _warnings.append(f"bank: account '{uid}' '{field}' is negative ({val})")


def check_shop_integrity():
    from helpers.database import shop_list
    try:
        items = shop_list()
    except Exception as e:
        _errors.append(f"shop database error: {e}")
        return
    if not items:
        _warnings.append("shop is empty -- no items available for purchase")
        return
    for row in items:
        key = row["key"]
        if not row.get("name", "").strip():
            _errors.append(f"shop item '{key}' has empty name")
        if not isinstance(row.get("price"), int) or row["price"] <= 0:
            _errors.append(f"shop item '{key}' has invalid price: {row.get('price')}")


def check_config_integrity():
    try:
        from helpers.config import load_config
        cfg = load_config()
    except Exception as e:
        _errors.append(f"config.yaml failed to load: {e}")
        return
    guild_id = cfg.get("guild_id")
    if not guild_id:
        _errors.append("config.yaml: guild_id is missing or 0")
    channels = cfg.get("channels", {})
    for key in REQUIRED_CHANNEL_KEYS:
        if key not in channels:
            _warnings.append(f"config.yaml: channel '{key}' not set")


def check_admins_integrity():
    if not os.path.exists(ADMINS_PATH):
        _warnings.append("admins.yaml not found -- no admins configured")
        return
    try:
        import yaml
        with open(ADMINS_PATH) as f:
            data = yaml.safe_load(f) or {}
        admins = data.get("admins", [])
        if not admins:
            _warnings.append("admins.yaml has empty admin list -- no one can use admin commands")
    except Exception as e:
        _errors.append(f"admins.yaml failed to parse: {e}")


def check_env_overrides():
    missing = []
    for key, label in [("DISCORD_TOKEN", "bot token"), ("PANEL_PIN", "panel PIN")]:
        if not os.getenv(key):
            missing.append(f"{key} ({label})")
    if missing:
        _warnings.append(f"env: missing -- {', '.join(missing)}")


def run_all() -> tuple[list[str], list[str]]:
    _errors.clear()
    _warnings.clear()
    check_data_directory()
    check_bank_integrity()
    check_shop_integrity()
    check_config_integrity()
    check_admins_integrity()
    check_env_overrides()
    return list(_errors), list(_warnings)


if __name__ == "__main__":
    sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))
    errors, warnings = run_all()
    for w in warnings:
        print(f"  [WARN] {w}")
    for e in errors:
        print(f"  [FAIL] {e}")
    if not errors and not warnings:
        print("  [OK] all data integrity checks passed")
    sys.exit(1 if errors else 0)
