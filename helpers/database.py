"""SQLite database backend replacing msgpack storage.

Thread-safe, WAL mode, auto-creates tables on first connect.
"""
import os
import sqlite3
import threading
import time
from typing import Any

DATA_DIR: str = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))
DB_PATH: str = os.path.join(DATA_DIR, "m4.db")

_local = threading.local()
_lock = threading.Lock()

REQUIRED_BANK_FIELDS = {
    "wallet", "bank", "debt",
    "last_work", "last_beg", "last_daily", "last_crime", "last_rob",
    "cf_wins", "cf_losses", "cf_net",
    "bj_wins", "bj_losses", "bj_pushes", "bj_net",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS bank (
    user_id INTEGER PRIMARY KEY,
    wallet INTEGER NOT NULL DEFAULT 100,
    bank INTEGER NOT NULL DEFAULT 0,
    debt INTEGER NOT NULL DEFAULT 0,
    last_work REAL NOT NULL DEFAULT 0,
    last_beg REAL NOT NULL DEFAULT 0,
    last_daily REAL NOT NULL DEFAULT 0,
    last_crime REAL NOT NULL DEFAULT 0,
    last_rob REAL NOT NULL DEFAULT 0,
    cf_wins INTEGER NOT NULL DEFAULT 0,
    cf_losses INTEGER NOT NULL DEFAULT 0,
    cf_net INTEGER NOT NULL DEFAULT 0,
    bj_wins INTEGER NOT NULL DEFAULT 0,
    bj_losses INTEGER NOT NULL DEFAULT 0,
    bj_pushes INTEGER NOT NULL DEFAULT 0,
    bj_net INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS shop_items (
    key TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    price INTEGER NOT NULL,
    role_id INTEGER
);

CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    item_key TEXT NOT NULL,
    item_name TEXT NOT NULL,
    purchased_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tx_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    kind TEXT NOT NULL,
    amount INTEGER NOT NULL,
    note TEXT DEFAULT '',
    at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS afk (
    user_id INTEGER PRIMARY KEY,
    reason TEXT DEFAULT 'afk',
    at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rps_scores (
    user_id INTEGER PRIMARY KEY,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    ties INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS reaction_roles (
    key TEXT PRIMARY KEY,
    role_id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS departed (
    user_id INTEGER PRIMARY KEY,
    left_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS warnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    reason TEXT DEFAULT '',
    moderator_id INTEGER DEFAULT 0,
    at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS blacklist (
    user_id INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS hof_posted (
    message_id INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS redeem_codes (
    code TEXT PRIMARY KEY,
    amount INTEGER NOT NULL,
    uses INTEGER NOT NULL DEFAULT 0,
    max_uses INTEGER NOT NULL,
    created_by INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS levels (
    user_id INTEGER PRIMARY KEY,
    xp INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS dumbass_scores (
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (guild_id, user_id)
);

PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=5000;
"""


def _conn() -> sqlite3.Connection:
    """Get thread-local connection."""
    if not hasattr(_local, "conn") or _local.conn is None:
        os.makedirs(DATA_DIR, exist_ok=True)
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.executescript(SCHEMA)
    return _local.conn


def close() -> None:
    if hasattr(_local, "conn") and _local.conn:
        _local.conn.close()
        _local.conn = None


# ── Bank ──────────────────────────────────────────────────────────

def bank_get(user_id: int) -> dict[str, Any]:
    conn = _conn()
    row = conn.execute("SELECT * FROM bank WHERE user_id = ?", (user_id,)).fetchone()
    if row:
        return dict(row)
    defaults = {"user_id": user_id, "wallet": 100, "bank": 0, "debt": 0,
                "last_work": 0, "last_beg": 0, "last_daily": 0,
                "last_crime": 0, "last_rob": 0,
                "cf_wins": 0, "cf_losses": 0, "cf_net": 0,
                "bj_wins": 0, "bj_losses": 0, "bj_pushes": 0, "bj_net": 0}
    conn.execute("""INSERT INTO bank (user_id) VALUES (?)""", (user_id,))
    conn.commit()
    return defaults


def bank_update(user_id: int, **fields) -> None:
    if not fields:
        return
    valid = {k: v for k, v in fields.items() if k in REQUIRED_BANK_FIELDS}
    if not valid:
        return
    set_clause = ", ".join(f"{k} = ?" for k in valid)
    vals = list(valid.values()) + [user_id]
    conn = _conn()
    conn.execute(f"UPDATE bank SET {set_clause} WHERE user_id = ?", vals)
    conn.commit()


def bank_all() -> dict[int, dict]:
    conn = _conn()
    rows = conn.execute("SELECT * FROM bank").fetchall()
    return {r["user_id"]: dict(r) for r in rows}


# ── Shop ───────────────────────────────────────────────────────────

def shop_list() -> dict[str, dict]:
    conn = _conn()
    rows = conn.execute("SELECT * FROM shop_items").fetchall()
    return {r["key"]: dict(r) for r in rows}


def shop_save(items: dict[str, dict]) -> None:
    conn = _conn()
    conn.execute("DELETE FROM shop_items")
    for key, item in items.items():
        conn.execute(
            "INSERT INTO shop_items (key, name, description, price, role_id) VALUES (?, ?, ?, ?, ?)",
            (key, item["name"], item["description"], item["price"], item.get("role")),
        )
    conn.commit()


# ── Inventory ──────────────────────────────────────────────────────

def inv_get(user_id: int) -> list[dict]:
    conn = _conn()
    rows = conn.execute(
        "SELECT id, item_key, item_name, purchased_at FROM inventory WHERE user_id = ? ORDER BY id",
        (user_id,),
    ).fetchall()
    return [{"item": r["item_key"], "name": r["item_name"], "purchased_at": r["purchased_at"]} for r in rows]


def inv_add(user_id: int, item_key: str, item_name: str) -> None:
    conn = _conn()
    conn.execute(
        "INSERT INTO inventory (user_id, item_key, item_name, purchased_at) VALUES (?, ?, ?, ?)",
        (user_id, item_key, item_name, time.strftime("%Y-%m-%dT%H:%M:%S")),
    )
    conn.commit()


def inv_remove(user_id: int, item_key: str) -> bool:
    conn = _conn()
    c = conn.execute(
        "DELETE FROM inventory WHERE user_id = ? AND item_key = ? LIMIT 1",
        (user_id, item_key),
    )
    conn.commit()
    return c.rowcount > 0


def inv_count(user_id: int) -> int:
    conn = _conn()
    return conn.execute("SELECT COUNT(*) FROM inventory WHERE user_id = ?", (user_id,)).fetchone()[0]


def inv_user_has(user_id: int, item_key: str) -> bool:
    conn = _conn()
    row = conn.execute(
        "SELECT 1 FROM inventory WHERE user_id = ? AND item_key = ? LIMIT 1",
        (user_id, item_key),
    ).fetchone()
    return row is not None


def inv_all() -> dict[int, list[dict]]:
    conn = _conn()
    rows = conn.execute("SELECT * FROM inventory ORDER BY user_id, id").fetchall()
    result: dict[int, list[dict]] = {}
    for r in rows:
        uid = r["user_id"]
        result.setdefault(uid, []).append({
            "item": r["item_key"],
            "name": r["item_name"],
            "purchased_at": r["purchased_at"],
        })
    return result


# ── Transaction History ────────────────────────────────────────────

def tx_add(user_id: int, kind: str, amount: int, note: str = "") -> None:
    conn = _conn()
    conn.execute(
        "INSERT INTO tx_history (user_id, kind, amount, note, at) VALUES (?, ?, ?, ?, ?)",
        (user_id, kind, amount, note, time.strftime("%Y-%m-%dT%H:%M:%S")),
    )
    # Keep only last 50 per user
    conn.execute(
        """DELETE FROM tx_history WHERE id NOT IN (
            SELECT id FROM tx_history WHERE user_id = ? ORDER BY id DESC LIMIT 50
        ) AND user_id = ?""",
        (user_id, user_id),
    )
    conn.commit()


def tx_get(user_id: int, limit: int = 20) -> list[dict]:
    conn = _conn()
    rows = conn.execute(
        "SELECT kind, amount, note, at FROM tx_history WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


# ── AFK ────────────────────────────────────────────────────────────

def afk_get(user_id: int) -> dict | None:
    conn = _conn()
    row = conn.execute("SELECT * FROM afk WHERE user_id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def afk_set(user_id: int, reason: str, at: str) -> None:
    conn = _conn()
    conn.execute(
        "INSERT OR REPLACE INTO afk (user_id, reason, at) VALUES (?, ?, ?)",
        (user_id, reason, at),
    )
    conn.commit()


def afk_remove(user_id: int) -> None:
    conn = _conn()
    conn.execute("DELETE FROM afk WHERE user_id = ?", (user_id,))
    conn.commit()


def afk_all() -> dict[int, dict]:
    conn = _conn()
    rows = conn.execute("SELECT * FROM afk").fetchall()
    return {r["user_id"]: dict(r) for r in rows}


# ── RPS Scores ─────────────────────────────────────────────────────

def rps_get(user_id: int) -> dict:
    conn = _conn()
    row = conn.execute("SELECT * FROM rps_scores WHERE user_id = ?", (user_id,)).fetchone()
    if row:
        return dict(row)
    defaults = {"user_id": user_id, "wins": 0, "losses": 0, "ties": 0}
    conn.execute("INSERT INTO rps_scores (user_id) VALUES (?)", (user_id,))
    conn.commit()
    return defaults


def rps_update(user_id: int, wins: int = 0, losses: int = 0, ties: int = 0) -> None:
    conn = _conn()
    conn.execute(
        "UPDATE rps_scores SET wins = wins + ?, losses = losses + ?, ties = ties + ? WHERE user_id = ?",
        (wins, losses, ties, user_id),
    )
    conn.commit()


# ── Reaction Roles ─────────────────────────────────────────────────

def rr_get(key: str) -> int | None:
    conn = _conn()
    row = conn.execute("SELECT role_id FROM reaction_roles WHERE key = ?", (key,)).fetchone()
    return row["role_id"] if row else None


def rr_set(key: str, role_id: int) -> None:
    conn = _conn()
    conn.execute("INSERT OR REPLACE INTO reaction_roles (key, role_id) VALUES (?, ?)", (key, role_id))
    conn.commit()


def rr_delete(key: str) -> None:
    conn = _conn()
    conn.execute("DELETE FROM reaction_roles WHERE key = ?", (key,))
    conn.commit()


def rr_all() -> dict[str, int]:
    conn = _conn()
    rows = conn.execute("SELECT * FROM reaction_roles").fetchall()
    return {r["key"]: r["role_id"] for r in rows}


# ── Departed (prune) ───────────────────────────────────────────────

def departed_get(user_id: int) -> float | None:
    conn = _conn()
    row = conn.execute("SELECT left_at FROM departed WHERE user_id = ?", (user_id,)).fetchone()
    return row["left_at"] if row else None


def departed_set(user_id: int, left_at: float) -> None:
    conn = _conn()
    conn.execute("INSERT OR REPLACE INTO departed (user_id, left_at) VALUES (?, ?)", (user_id, left_at))
    conn.commit()


def departed_remove(user_id: int) -> None:
    conn = _conn()
    conn.execute("DELETE FROM departed WHERE user_id = ?", (user_id,))
    conn.commit()


def departed_all() -> dict[int, float]:
    conn = _conn()
    rows = conn.execute("SELECT * FROM departed").fetchall()
    return {r["user_id"]: r["left_at"] for r in rows}


def departed_expire(before: float) -> list[int]:
    conn = _conn()
    rows = conn.execute("SELECT user_id FROM departed WHERE left_at < ?", (before,)).fetchall()
    uids = [r["user_id"] for r in rows]
    if uids:
        conn.execute("DELETE FROM departed WHERE left_at < ?", (before,))
        conn.commit()
    return uids


# ── Warnings ───────────────────────────────────────────────────────

def warn_add(guild_id: int, user_id: int, reason: str, moderator_id: int) -> int:
    conn = _conn()
    c = conn.execute(
        "INSERT INTO warnings (guild_id, user_id, reason, moderator_id, at) VALUES (?, ?, ?, ?, ?)",
        (guild_id, user_id, reason, moderator_id, time.time()),
    )
    conn.commit()
    return c.lastrowid


def warn_count(guild_id: int, user_id: int) -> int:
    conn = _conn()
    row = conn.execute(
        "SELECT COUNT(*) FROM warnings WHERE guild_id = ? AND user_id = ?",
        (guild_id, user_id),
    ).fetchone()
    return row[0]


def warn_list(guild_id: int, user_id: int) -> list[dict]:
    conn = _conn()
    rows = conn.execute(
        "SELECT id, reason, moderator_id, at FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY id",
        (guild_id, user_id),
    ).fetchall()
    return [dict(r) for r in rows]


def warn_remove(warn_id: int) -> bool:
    conn = _conn()
    c = conn.execute("DELETE FROM warnings WHERE id = ?", (warn_id,))
    conn.commit()
    return c.rowcount > 0


# ── Blacklist ──────────────────────────────────────────────────────

def blacklist_add(user_id: int) -> None:
    conn = _conn()
    conn.execute("INSERT OR IGNORE INTO blacklist (user_id) VALUES (?)", (user_id,))
    conn.commit()


def blacklist_remove(user_id: int) -> None:
    conn = _conn()
    conn.execute("DELETE FROM blacklist WHERE user_id = ?", (user_id,))
    conn.commit()


def blacklist_has(user_id: int) -> bool:
    conn = _conn()
    row = conn.execute("SELECT 1 FROM blacklist WHERE user_id = ?", (user_id,)).fetchone()
    return row is not None


def blacklist_all() -> list[int]:
    conn = _conn()
    rows = conn.execute("SELECT user_id FROM blacklist").fetchall()
    return [r["user_id"] for r in rows]


# ── Hall of Fame ───────────────────────────────────────────────────

def hof_has(message_id: int) -> bool:
    conn = _conn()
    row = conn.execute("SELECT 1 FROM hof_posted WHERE message_id = ?", (message_id,)).fetchone()
    return row is not None


def hof_add(message_id: int) -> None:
    conn = _conn()
    conn.execute("INSERT OR IGNORE INTO hof_posted (message_id) VALUES (?)", (message_id,))
    conn.commit()


def hof_all() -> set[int]:
    conn = _conn()
    rows = conn.execute("SELECT message_id FROM hof_posted").fetchall()
    return {r["message_id"] for r in rows}


# ── Redeem Codes ────────────────────────────────────────────────────

def codes_get(code: str) -> dict | None:
    conn = _conn()
    row = conn.execute("SELECT * FROM redeem_codes WHERE code = ?", (code,)).fetchone()
    return dict(row) if row else None


def codes_set(code: str, amount: int, max_uses: int, created_by: int) -> None:
    conn = _conn()
    conn.execute(
        "INSERT OR REPLACE INTO redeem_codes (code, amount, max_uses, created_by) VALUES (?, ?, ?, ?)",
        (code, amount, max_uses, created_by),
    )
    conn.commit()


def codes_use(code: str) -> bool:
    conn = _conn()
    row = conn.execute("SELECT uses, max_uses FROM redeem_codes WHERE code = ?", (code,)).fetchone()
    if not row or row["uses"] >= row["max_uses"]:
        return False
    conn.execute("UPDATE redeem_codes SET uses = uses + 1 WHERE code = ?", (code,))
    conn.commit()
    return True


def codes_delete(code: str) -> None:
    conn = _conn()
    conn.execute("DELETE FROM redeem_codes WHERE code = ?", (code,))
    conn.commit()


def codes_all() -> dict[str, dict]:
    conn = _conn()
    rows = conn.execute("SELECT * FROM redeem_codes").fetchall()
    return {r["code"]: dict(r) for r in rows}


# ── Levels ──────────────────────────────────────────────────────────

def level_get(user_id: int) -> dict:
    conn = _conn()
    row = conn.execute("SELECT * FROM levels WHERE user_id = ?", (user_id,)).fetchone()
    if row:
        return dict(row)
    conn.execute("INSERT INTO levels (user_id) VALUES (?)", (user_id,))
    conn.commit()
    return {"user_id": user_id, "xp": 0, "level": 1}


def level_update(user_id: int, xp: int = 0, level: int = 0) -> None:
    conn = _conn()
    conn.execute(
        "UPDATE levels SET xp = xp + ?, level = ? WHERE user_id = ?",
        (xp, level, user_id),
    )
    conn.commit()


def level_all() -> dict[int, dict]:
    conn = _conn()
    rows = conn.execute("SELECT * FROM levels").fetchall()
    return {r["user_id"]: dict(r) for r in rows}


# ── Dumbass Scores ──────────────────────────────────────────────────

def dumbass_get(guild_id: int, user_id: int) -> int:
    conn = _conn()
    row = conn.execute(
        "SELECT count FROM dumbass_scores WHERE guild_id = ? AND user_id = ?",
        (guild_id, user_id),
    ).fetchone()
    return row["count"] if row else 0


def dumbass_increment(guild_id: int, user_id: int) -> int:
    conn = _conn()
    conn.execute(
        "INSERT INTO dumbass_scores (guild_id, user_id, count) VALUES (?, ?, 1) "
        "ON CONFLICT(guild_id, user_id) DO UPDATE SET count = count + 1",
        (guild_id, user_id),
    )
    conn.commit()
    row = conn.execute(
        "SELECT count FROM dumbass_scores WHERE guild_id = ? AND user_id = ?",
        (guild_id, user_id),
    ).fetchone()
    return row["count"] if row else 1


def dumbass_leaderboard(guild_id: int, limit: int = 10) -> list[dict]:
    conn = _conn()
    rows = conn.execute(
        "SELECT user_id, count FROM dumbass_scores WHERE guild_id = ? ORDER BY count DESC LIMIT ?",
        (guild_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]
