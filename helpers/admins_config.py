import yaml
import os
from typing import Set, Any

ADMINS_FILE: str = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "admins.yaml"))
DEFAULT_ADMINS: Set[int] = {779653730978103306, 500683600614785025}

def load_admins() -> Set[int]:
    if not os.path.exists(ADMINS_FILE):
        save_admins(DEFAULT_ADMINS)
        return DEFAULT_ADMINS
    with open(ADMINS_FILE, "r") as f:
        data: Any = yaml.safe_load(f) or {}
    return set(data.get("admins", []))

def save_admins(admins: Set[int]) -> None:
    with open(ADMINS_FILE, "w") as f:
        yaml.dump({"admins": sorted(admins)}, f)

def is_admin(user_id: int) -> bool:
    return user_id in load_admins()
