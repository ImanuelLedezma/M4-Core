import discord
from discord.ext import commands
from helpers.storage import load, save

HISTORY_FILE = "tx_history.msgpack"

def add_tx(user_id: int, kind: str, amount: int, note: str = "") -> None:
    data = load(HISTORY_FILE)
    uid = str(user_id)
    if uid not in data:
        data[uid] = []
    data[uid].append({
        "kind": kind,
        "amount": amount,
        "note": note,
        "at": discord.utils.utcnow().isoformat(),
    })
    if len(data[uid]) > 50:
        data[uid] = data[uid][-50:]
    save(HISTORY_FILE, data)

def add_tx_sync(user_id: int, kind: str, amount: int, note: str = "") -> None:
    import time
    data = load(HISTORY_FILE)
    uid = str(user_id)
    if uid not in data:
        data[uid] = []
    data[uid].append({
        "kind": kind,
        "amount": amount,
        "note": note,
        "at": time.time(),
    })
    if len(data[uid]) > 50:
        data[uid] = data[uid][-50:]
    save(HISTORY_FILE, data)

class History(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="history", aliases=["tx", "transactions"], description="show your recent transaction history", help="Shows your last 20 economy transactions including earnings, losses, transfers, and purchases.")
    async def history(self, ctx):
        data = load(HISTORY_FILE)
        uid = str(ctx.author.id)
        entries = data.get(uid, [])
        if not entries:
            return await ctx.send(embed=discord.Embed(
                description="no transaction history yet.",
                color=0x2b2d31
            ))

        embed = discord.Embed(title="◈ transaction history", color=0x2b2d31)
        for entry in entries[-20:]:
            ts = entry.get("at", "")
            if isinstance(ts, str):
                ts = ts[:19].replace("T", " ")
            else:
                ts = ""
            kind = entry["kind"]
            amount = entry["amount"]
            sign = "+" if amount >= 0 else ""
            icon = {"earn": "√", "loss": "⊘", "transfer": "╼", "purchase": "◈", "admin": "⚙"}.get(kind, "·")
            note = f" · {entry['note']}" if entry.get("note") else ""
            embed.add_field(
                name=f"{icon} {kind.title()} {sign}{amount:,}",
                value=f"{ts}{note}",
                inline=False,
            )
        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(History(bot))
