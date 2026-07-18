import discord
from discord.ext import commands
from helpers.economy_base import load_bank, open_account, _ratelimit, RATE_LIMIT_COMMANDS, RATE_LIMIT_WINDOW

class Balance(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    def _rate_status(self, user_id: int) -> str:
        import time
        now = time.time()
        window = [t for t in _ratelimit.get(user_id, []) if now - t < RATE_LIMIT_WINDOW]
        remaining = RATE_LIMIT_COMMANDS - len(window)
        bar = "█" * len(window) + "░" * (RATE_LIMIT_COMMANDS - len(window))
        return f"`[{bar}]` {remaining}/{RATE_LIMIT_COMMANDS} commands available"

    @commands.hybrid_command(name="balance", aliases=["bal"], description="check your current wallet and bank", help="Shows your wallet balance, bank savings, total cores, and any debt. Check another user by mentioning them: !balance @user")
    async def balance(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        data = load_bank()
        data = open_account(member.id, data)

        uid = str(member.id)
        wallet = data[uid]["wallet"]
        bank = data[uid]["bank"]
        debt = data[uid]["debt"]
        net = wallet + bank - debt

        embed = discord.Embed(
            title=f"╼ {member.display_name.lower()}'s ledger ╾",
            color=0xff4500 if debt > 0 else 0x2b2d31
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="◈ wallet", value=f"⌬ {wallet:,}", inline=True)
        embed.add_field(name="◈ bank", value=f"⌬ {bank:,}", inline=True)
        embed.add_field(name="▼ total", value=f"**⌬ {wallet + bank:,}**", inline=False)
        if debt > 0:
            embed.add_field(name="⊘ debt", value=f"**⌬ {debt:,}**", inline=True)
            embed.add_field(name="▼ net worth", value=f"⌬ {net:,}", inline=True)
        embed.set_footer(text=f"requested by {ctx.author.display_name} · {self._rate_status(ctx.author.id)}")
        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Balance(bot))