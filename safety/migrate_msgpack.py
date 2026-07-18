"""Migrate existing MSGPACK data files to SQLite.

Run once after updating. Renames old .msgpack files to .bak
so the bot falls back to DB on next startup.

Usage: python -m safety.migrate_msgpack
"""
import os
import sys
import time

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))

DATA_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data"))

_state = {"migrated": 0, "errors": 0}


def _msgpack_path(name):
    return os.path.join(DATA_DIR, name)


def _load_msgpack(name):
    import msgpack
    path = _msgpack_path(name)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as f:
            data = msgpack.unpackb(f.read(), raw=False)
            return data if data else {}
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        _state["errors"] += 1
        return None


def _backup(name):
    src = _msgpack_path(name)
    bak = src + ".bak"
    if os.path.exists(src):
        os.rename(src, bak)
        print(f"    backed up -> {name}.bak")


def migrate_bank():
    from helpers.database import bank_get, bank_update
    data = _load_msgpack("bank.msgpack")
    if data is None: return
    if not isinstance(data, dict): return
    for uid_str, acct in data.items():
        if not isinstance(acct, dict): continue
        try: uid = int(uid_str)
        except ValueError: continue
        bank_get(uid)
        fields = {k: v for k, v in acct.items()
                  if k in ("wallet","bank","debt","last_work","last_beg","last_daily",
                           "last_crime","last_rob","cf_wins","cf_losses","cf_net",
                           "bj_wins","bj_losses","bj_pushes","bj_net")}
        if fields: bank_update(uid, **fields)
    _backup("bank.msgpack")
    _state["migrated"] += 1


def migrate_shop():
    from helpers.database import shop_save
    data = _load_msgpack("shop.msgpack")
    if data is None: return
    if isinstance(data, dict): shop_save(data); _backup("shop.msgpack"); _state["migrated"] += 1; return
    from commands.economy.shop import SHOP_ITEMS
    shop_save(SHOP_ITEMS)


def migrate_inventory():
    from helpers.database import inv_add
    data = _load_msgpack("inventory.msgpack")
    if data is None or not isinstance(data, dict): return
    for uid_str, items in data.items():
        if not isinstance(items, list): continue
        try: uid = int(uid_str)
        except ValueError: continue
        for entry in items:
            if isinstance(entry, dict): inv_add(uid, entry.get("item",""), entry.get("name",""))
    _backup("inventory.msgpack"); _state["migrated"] += 1


def migrate_tx_history():
    from helpers.database import tx_add
    data = _load_msgpack("tx_history.msgpack")
    if data is None or not isinstance(data, dict): return
    for uid_str, entries in data.items():
        if not isinstance(entries, list): continue
        try: uid = int(uid_str)
        except ValueError: continue
        for e in entries:
            if isinstance(e, dict): tx_add(uid, e.get("kind","unknown"), e.get("amount",0), e.get("note",""))
    _backup("tx_history.msgpack"); _state["migrated"] += 1


def migrate_afk():
    from helpers.database import afk_set
    data = _load_msgpack("afk.msgpack")
    if data is None or not isinstance(data, dict): return
    for uid_str, entry in data.items():
        if not isinstance(entry, dict): continue
        try: uid = int(uid_str)
        except ValueError: continue
        afk_set(uid, entry.get("reason","afk"), entry.get("at", time.strftime("%Y-%m-%dT%H:%M:%S")))
    _backup("afk.msgpack"); _state["migrated"] += 1


def migrate_rps():
    from helpers.database import rps_get, rps_update
    data = _load_msgpack("rps.msgpack")
    if data is None or not isinstance(data, dict): return
    for uid_str, stats in data.items():
        if not isinstance(stats, dict): continue
        try: uid = int(uid_str)
        except ValueError: continue
        rps_get(uid); rps_update(uid, stats.get("wins",0), stats.get("losses",0), stats.get("ties",0))
    _backup("rps.msgpack"); _state["migrated"] += 1


def migrate_reaction_roles():
    from helpers.database import rr_set
    data = _load_msgpack("reaction_roles.msgpack")
    if data is None or not isinstance(data, dict): return
    for key, role_id in data.items(): rr_set(key, role_id)
    _backup("reaction_roles.msgpack"); _state["migrated"] += 1


def migrate_departed():
    from helpers.database import departed_set
    data = _load_msgpack("departed.msgpack")
    if data is None or not isinstance(data, dict): return
    for uid_str, left_at in data.items():
        try: uid = int(uid_str)
        except ValueError: continue
        departed_set(uid, left_at)
    _backup("departed.msgpack"); _state["migrated"] += 1


def migrate_warnings():
    from helpers.database import warn_add
    data = _load_msgpack("warnings.msgpack")
    if data is None or not isinstance(data, dict): return
    for guild_str, users in data.items():
        try: gid = int(guild_str)
        except ValueError: continue
        if not isinstance(users, dict): continue
        for uid_str, warns in users.items():
            try: uid = int(uid_str)
            except ValueError: continue
            if not isinstance(warns, list): continue
            for w in warns:
                if isinstance(w, dict): warn_add(gid, uid, w.get("reason",""), w.get("mod",0))
    _backup("warnings.msgpack"); _state["migrated"] += 1


def migrate_blacklist():
    from helpers.database import blacklist_add
    data = _load_msgpack("blacklist.msgpack")
    if data is None: return
    items = data if isinstance(data, list) else (list(data) if isinstance(data, set) else [])
    for uid in items:
        if isinstance(uid, int): blacklist_add(uid)
    _backup("blacklist.msgpack"); _state["migrated"] += 1


def migrate_hof():
    from helpers.database import hof_add
    data = _load_msgpack("hof_posted.msgpack")
    if data is None: return
    items = data if isinstance(data, list) else (list(data) if isinstance(data, set) else [])
    for mid in items:
        if isinstance(mid, int): hof_add(mid)
    _backup("hof_posted.msgpack"); _state["migrated"] += 1


def migrate_codes():
    from helpers.database import codes_set
    data = _load_msgpack("codes.msgpack")
    if data is None or not isinstance(data, dict): return
    for key, entry in data.items():
        if isinstance(entry, dict): codes_set(key, entry.get("amount",0), entry.get("uses",0), entry.get("created_by",0))
    _backup("codes.msgpack"); _state["migrated"] += 1


def migrate_levels():
    from helpers.database import level_get, level_update
    data = _load_msgpack("levels.msgpack")
    if data is None or not isinstance(data, dict): return
    for uid_str, entry in data.items():
        if not isinstance(entry, dict): continue
        try: uid = int(uid_str)
        except ValueError: continue
        level_get(uid); level_update(uid, entry.get("xp",0), entry.get("level",1))
    _backup("levels.msgpack"); _state["migrated"] += 1


def migrate_dumbass():
    from helpers.database import dumbass_increment
    data = _load_msgpack("dumbass.msgpack")
    if data is None or not isinstance(data, dict): return
    for gid_str, users in data.items():
        if not isinstance(users, dict): continue
        try: gid = int(gid_str)
        except ValueError: continue
        for uid_str, count in users.items():
            if not isinstance(count, (int, float)): continue
            try: uid = int(uid_str)
            except ValueError: continue
            for _ in range(int(count)): dumbass_increment(gid, uid)
    _backup("dumbass.msgpack"); _state["migrated"] += 1


MIGRATORS = [
    ("bank.msgpack", migrate_bank),
    ("shop.msgpack", migrate_shop),
    ("inventory.msgpack", migrate_inventory),
    ("tx_history.msgpack", migrate_tx_history),
    ("afk.msgpack", migrate_afk),
    ("rps.msgpack", migrate_rps),
    ("reaction_roles.msgpack", migrate_reaction_roles),
    ("departed.msgpack", migrate_departed),
    ("warnings.msgpack", migrate_warnings),
    ("blacklist.msgpack", migrate_blacklist),
    ("hof_posted.msgpack", migrate_hof),
    ("codes.msgpack", migrate_codes),
    ("levels.msgpack", migrate_levels),
    ("dumbass.msgpack", migrate_dumbass),
]


def main():
    print("  migrating MSGPACK -> SQLite...\n")
    for name, migrator in MIGRATORS:
        path = _msgpack_path(name)
        if os.path.exists(path):
            print(f"  [{name}]")
            migrator()
        else:
            print(f"  [{name}] not found, skipping")
    print(f"\n  done: {_state["migrated"]} files migrated, {_state["errors"]} errors")
    return 0 if _state["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
