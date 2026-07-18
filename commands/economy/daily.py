import discord
import random
import time
from discord.ext import commands
from helpers.economy_base import load_bank, save_bank, open_account, get_cooldown, set_cooldown, apply_earnings, debt_prompt

COOLDOWN = 86400
STREAK_BONUS = 50
MAX_STREAK = 30

class Daily(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    def _get_streak(self, data: dict, uid: str) -> int:
        last = data[uid].get("last_daily", 0)
        if not last:
            return 0
        if time.time() - last < COOLDOWN * 2:
            return data[uid].get("daily_streak", 0)
        return 0

    @commands.hybrid_command(name="daily", description="claim your daily allowance of cores", help="Claim 100-300 cores daily. Build a streak by claiming every day — each consecutive day adds +50 bonus (max 30 days = +1500 bonus!). Resets if you miss a day.")
    async def daily(self, ctx):
        data = load_bank()
        data = open_account(ctx.author.id, data)
        uid = str(ctx.author.id)

        data = await debt_prompt(ctx, self.bot, data, ctx.author.id)

        remaining = get_cooldown(ctx.author.id, data, "last_daily", COOLDOWN)
        if remaining:
            hours = round(remaining / 3600, 1)
            mins = round((remaining % 3600) / 60)
            return await ctx.send(embed=discord.Embed(
                description=f"⧖ come back in {int(hours)}h {mins}m", color=0xff4500
            ), ephemeral=True)

        base = random.randint(100, 300)
        streak = self._get_streak(data, uid) + 1
        if streak > MAX_STREAK:
            streak = MAX_STREAK

        streak_earnings = streak * STREAK_BONUS
        earnings = base + streak_earnings

        debt_paid, _ = apply_earnings(uid, data, earnings)
        data[uid]["daily_streak"] = streak
        set_cooldown(ctx.author.id, data, "last_daily")
        save_bank(data)

        desc = f"╼ **daily reward** ╾\n\nbase: **⌬ {base:,}**"
        if streak_earnings:
            desc += f"\n🔥 streak bonus (×{streak}): **+⌬ {streak_earnings:,}**"
        desc += f"\n\n═══════════════\ntotal: **⌬ {earnings:,}**"
        if debt_paid:
            desc += f"\n⌬ {debt_paid:,} went toward your debt"

        embed = discord.Embed(description=desc, color=0xeb459e)
        embed.set_footer(text=f"daily streak: {streak} · wallet: {data[uid]['wallet']:,} cores")
        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Daily(bot))