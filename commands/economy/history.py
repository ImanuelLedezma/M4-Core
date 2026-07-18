import discord
from discord.ext import commands
from helpers.database import tx_add, tx_get

class History(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="history", aliases=["tx", "transactions"], description="show your recent transaction history", help="Shows your last 20 economy transactions including earnings, losses, transfers, and purchases.")
    async def history(self, ctx):
        entries = tx_get(ctx.author.id)
        if not entries:
            return await ctx.send(embed=discord.Embed(
                description="no transaction history yet.",
                color=0x2b2d31
            ))

        embed = discord.Embed(title="◈ transaction history", color=0x2b2d31)
        for entry in entries[-20:]:
            kind = entry["kind"]
            amount = entry["amount"]
            sign = "+" if amount >= 0 else ""
            icon = {"earn": "√", "loss": "⊘", "transfer": "╼", "purchase": "◈", "admin": "⚙"}.get(kind, "·")
            note = f" · {entry['note']}" if entry.get("note") else ""
            embed.add_field(
                name=f"{icon} {kind.title()} {sign}{amount:,}",
                value=f"{entry['at']}{note}",
                inline=False,
            )
        await ctx.send(embed=embed)


def add_tx(user_id: int, kind: str, amount: int, note: str = "") -> None:
    tx_add(user_id, kind, amount, note)


def add_tx_sync(user_id: int, kind: str, amount: int, note: str = "") -> None:
    tx_add(user_id, kind, amount, note)


async def setup(bot) -> None:
    await bot.add_cog(History(bot))
