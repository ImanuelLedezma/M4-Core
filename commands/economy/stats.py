import discord
from discord.ext import commands
from helpers.economy_base import load_bank

class Stats(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="leaderboard", aliases=["lb", "top", "rich"], description="view the richest users", help="Shows the top 10 richest users by net worth (wallet + bank - debt). Use !leaderboard 2 for next page. Medals for top 3.")
    async def leaderboard(self, ctx, page: int = 1):
        data = load_bank()
        if not data:
            return await ctx.send(embed=discord.Embed(description="no economy data yet.", color=0x2b2d31))

        sorted_users = sorted(data.items(), key=lambda x: x[1].get("wallet", 0) + x[1].get("bank", 0) - x[1].get("debt", 0), reverse=True)

        per_page = 10
        total_pages = (len(sorted_users) + per_page - 1) // per_page
        page = max(1, min(page, total_pages))
        start = (page - 1) * per_page
        end = start + per_page

        embed = discord.Embed(
            title="╼ core leaderboard ╾",
            description=f"page {page}/{total_pages} · {len(sorted_users)} total accounts",
            color=0x2b2d31
        )

        medals = ["🥇", "🥈", "🥉"]
        for i, (user_id, acc) in enumerate(sorted_users[start:end], start + 1):
            user = self.bot.get_user(int(user_id))
            if not user:
                try:
                    user = await self.bot.fetch_user(int(user_id))
                except discord.NotFound:
                    user = None
            name = user.display_name if user else f"unknown ({user_id})"
            total = acc["wallet"] + acc["bank"]
            debt = acc.get("debt", 0)
            net = total - debt
            prefix = medals[i - 1] if i <= 3 else f"`{i}.`"
            debt_str = f" (⌬ {debt:,} debt)" if debt else ""
            embed.add_field(
                name=f"{prefix} {name}",
                value=f"⌬ {total:,}{debt_str} · net: ⌬ {net:,}",
                inline=False
            )

        embed.set_footer(text="use !leaderboard 2 for next page")
        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Stats(bot))