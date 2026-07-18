from helpers.database import blacklist_has, blacklist_add, blacklist_remove, blacklist_all

def load_blacklist() -> set[int]:
    return set(blacklist_all())

def save_blacklist(blacklist: set[int]) -> None:
    current = set(blacklist_all())
    for uid in blacklist - current:
        blacklist_add(uid)
    for uid in current - blacklist:
        blacklist_remove(uid)

def is_blacklisted(user_id: int) -> bool:
    return blacklist_has(user_id)
