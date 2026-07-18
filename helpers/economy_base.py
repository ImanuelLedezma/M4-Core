import os
import time
import asyncio
import threading
import discord
from collections import defaultdict
from typing import Dict, Any, Tuple
from discord.ext import commands
from helpers.storage import load, save
from commands.economy.history import add_tx_sync

BANK_FILE = "bank.msgpack"
AccountData = Dict[str, Any]
_bank_lock = threading.Lock()

RATE_LIMIT_COMMANDS = 5
RATE_LIMIT_WINDOW = 10
_ratelimit: Dict[int, list[float]] = defaultdict(list)
_cache: AccountData = {}
_cache_mtime: float = 0

def check_ratelimit(user_id: int) -> bool:
    now = time.time()
    _ratelimit[user_id] = [t for t in _ratelimit[user_id] if now - t < RATE_LIMIT_WINDOW]
    if len(_ratelimit[user_id]) >= RATE_LIMIT_COMMANDS:
        return True
    _ratelimit[user_id].append(now)
    return False

def _bank_path() -> str:
    from helpers.storage import DATA_DIR
    return os.path.join(DATA_DIR, BANK_FILE)

def load_bank() -> AccountData:
    global _cache_mtime
    with _bank_lock:
        try:
            mtime = os.path.getmtime(_bank_path())
        except OSError:
            mtime = 0
        if not _cache or mtime > _cache_mtime:
            _cache.clear()
            _cache.update(load(BANK_FILE))
            _cache_mtime = mtime
        return _cache

def save_bank(data: AccountData) -> None:
    global _cache_mtime
    with _bank_lock:
        if data is not _cache:
            _cache.clear()
            _cache.update(data)
        save(BANK_FILE, data)
        try:
            _cache_mtime = os.path.getmtime(_bank_path())
        except OSError:
            _cache_mtime = 0
    
def open_account(user_id: int, data: AccountData) -> AccountData:
    user_id = int(user_id)
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "wallet": 100,
            "bank": 0,
            "debt": 0,
            "last_work": 0,
            "last_beg": 0,
            "last_daily": 0,
            "last_crime": 0,
            "last_rob": 0,
        }
        save_bank(data)
    else:
        changed = False
        for key in ("last_work", "last_beg", "last_daily", "last_crime", "last_rob"):
            if key not in data[uid]:
                data[uid][key] = 0
                changed = True
        if "debt" not in data[uid]:
            data[uid]["debt"] = 0
            changed = True
        if changed:
            save_bank(data)
    return data

def get_cooldown(user_id: int, data: AccountData, key: str, seconds: int) -> int:
    current_time = time.time()
    last_time = data[str(int(user_id))].get(key, 0)
    remaining = (last_time + seconds) - current_time
    return max(0, round(remaining))

def set_cooldown(user_id: int, data: AccountData, key: str) -> None:
    data[str(user_id)][key] = time.time()

def apply_loss(user_id: int, data: AccountData, amount: int, note: str = "") -> None:
    uid = str(int(user_id))
    wallet = data[uid]["wallet"]
    if amount <= wallet:
        data[uid]["wallet"] -= amount
    else:
        data[uid]["debt"] += amount - wallet
        data[uid]["wallet"] = 0
    add_tx_sync(user_id, "loss", -amount, note)

def apply_earnings(user_id: int, data: AccountData, amount: int, note: str = "") -> Tuple[int, int]:
    uid = str(int(user_id))
    debt = data[uid]["debt"]
    if debt > 0:
        if amount >= debt:
            data[uid]["debt"] = 0
            data[uid]["wallet"] += amount - debt
            add_tx_sync(user_id, "earn", amount, note)
            return debt, amount - debt
        else:
            data[uid]["debt"] -= amount
            add_tx_sync(user_id, "earn", amount, note)
            return amount, 0
    else:
        data[uid]["wallet"] += amount
        add_tx_sync(user_id, "earn", amount, note)
        return 0, amount

async def debt_prompt(ctx: commands.Context, bot: commands.Bot, data: AccountData, user_id: int) -> AccountData:
    uid = str(user_id)
    debt = data[uid]["debt"]
    if debt == 0:
        return data

    bank = data[uid]["bank"]

    if bank > 0:
        desc = (
            f"you're **⌬ {debt:,}** in debt, and you have **⌬ {bank:,}** in your bank\n\n"
            f"would you like to pay off your debt with your bank balance to the extent possible?"
        )
    else:
        desc = f"you're **⌬ {debt:,}** in debt.\n\ncontinuing..."

    embed = discord.Embed(title="◈ in debt", description=desc, color=0xff4500)
    msg = await ctx.send(embed=embed)

    if bank == 0:
        return data

    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    def check(reaction, user):
        return (
            user.id == ctx.author.id
            and reaction.message.id == msg.id
            and str(reaction.emoji) in ("✅", "❌")
        )

    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=30.0, check=check)
    except asyncio.TimeoutError:
        await msg.edit(embed=discord.Embed(
            title="◈ in debt",
            description="⧖ timed out, continuing in debt",
            color=0xff4500
        ))
        try:
            await msg.clear_reactions()
        except (discord.Forbidden, discord.NotFound):
            pass
        return data

    try:
        await msg.clear_reactions()
    except (discord.Forbidden, discord.NotFound):
        pass

    if str(reaction.emoji) == "✅":
        paid = min(bank, debt)
        data[uid]["bank"] -= paid
        data[uid]["debt"] -= paid
        remaining = data[uid]["debt"]
        if remaining == 0:
            result = f"√ paid off **⌬ {paid:,}** — debt cleared!"
        else:
            result = f"√ paid **⌬ {paid:,}** from bank — **⌬ {remaining:,}** still owed"
        await msg.edit(embed=discord.Embed(title="◈ in debt", description=result, color=0x57f287))
        save_bank(data)
    else:
        await msg.edit(embed=discord.Embed(
            title="◈ in debt",
            description=f"✖ staying in debt, **⌬ {debt:,}** owed",
            color=0xff4500
        ))

    return data
