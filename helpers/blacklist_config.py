from typing import Set, Any
from helpers.storage import load, save

BLACKLIST_FILE: str = "blacklist.msgpack"

def load_blacklist() -> Set[int]:
    data: Any = load(BLACKLIST_FILE)
    return set(data) if data else set()

def save_blacklist(blacklist: Set[int]) -> None:
    save(BLACKLIST_FILE, list(blacklist))

def is_blacklisted(user_id: int) -> bool:
    return user_id in load_blacklist()
