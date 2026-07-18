"""Data integrity sanity checks run at startup.

Catches corrupted msgpack files, invalid balances, missing required data,
and other issues that would otherwise surface as confusing runtime errors.
"""
import os
import sys
import math

DATA_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))
CONFIG_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.yaml"))
ADMINS_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "admins.yaml"))
ENV_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))
REQUIRED_CHANNEL_KEYS = ("log", "console", "ai_chat", "dictionary", "confession", "hall_of_fame", "welcome")

_errors: list[str] = []
_warnings: list[str] = []


def _load_msgpack(name: str):
    from helpers.storage import load
    try:
        return load(name)
    except Exception as e:
        _errors.append(f"corrupt {name}: {e}")
        return None


def check_data_directory():
    if not os.path.isdir(DATA_DIR):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            _warnings.append(f"created missing data directory at {DATA_DIR}")
        except OSError as e:
            _errors.append(f"cannot create data directory {DATA_DIR}: {e}")


def check_bank_integrity():
    bank = _load_msgpack("bank.msgpack")
    if bank is None:
        return
    if not isinstance(bank, dict):
        _errors.append("bank.msgpack is not a dict -- data corrupted")
        return
    for uid, acct in bank.items():
        if not isinstance(acct, dict):
            _errors.append(f"bank: account '{uid}' is not a dict -- possible corruption")
            continue
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
        for ts_field in ("last_work", "last_beg", "last_daily", "last_crime", "last_rob"):
            ts = acct.get(ts_field)
            if ts is not None and not isinstance(ts, (int, float)):
                _warnings.append(f"bank: account '{uid}' '{ts_field}' has unexpected type {type(ts).__name__}")


def check_shop_integrity():
    from commands.economy.shop import load_shop
    try:
        items = load_shop()
    except Exception as e:
        _errors.append(f"shop data failed to load: {e}")
        return
    if not items:
        _warnings.append("shop is empty -- no items available for purchase")
        return
    for key, item in items.items():
        if not isinstance(item, dict):
            _errors.append(f"shop item '{key}' is not a dict")
            continue
        for field in ("name", "description", "price", "role"):
            if field not in item:
                _errors.append(f"shop item '{key}' missing '{field}'")
        price = item.get("price")
        if price is not None and (not isinstance(price, int) or price <= 0):
            _errors.append(f"shop item '{key}' has invalid price: {price}")
        if not item.get("name", "").strip():
            _errors.append(f"shop item '{key}' has empty name")


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
    lock_cfg = cfg.get("lock", {})
    if lock_cfg and "revoke_roles" in lock_cfg and not isinstance(lock_cfg["revoke_roles"], list):
        _errors.append("config.yaml: 'lock.revoke_roles' should be a list")


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
        for a in admins:
            if not isinstance(a, int):
                _warnings.append(f"admins.yaml: '{a}' is not a valid user ID (should be int)")
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
