import discord
import random
from discord.ext import commands
from helpers.economy_base import load_bank, save_bank, open_account, get_cooldown, set_cooldown, apply_earnings, debt_prompt

COOLDOWN = 180

JOBS = [
    ("system maintenance", 300, 850),
    ("data mining", 350, 800),
    ("protocol optimization", 400, 750),
    ("freelancing", 350, 900),
    ("consulting", 450, 850),
    ("programming", 400, 800),
    ("video editing", 300, 700),
    ("graphic design", 350, 750),
    ("tutoring", 250, 600),
    ("content creation", 300, 700),
    ("dog walking", 200, 500),
    ("lawn mowing", 250, 550),
    ("accounting", 400, 700),
    ("customer support", 250, 550),
]

JACKPOT_JOBS = [
    ("winning a hackathon", 3000, 5000),
    ("cashing out crypto early", 4000, 8000),
    ("landing a big client", 5000, 10000),
    ("discovering a zero-day exploit", 6000, 12000),
    ("winning the lottery", 10000, 25000),
]

JACKPOT_CHANCE = 0.05
STREAK_MULTIPLIER = 1.5
STREAK_THRESHOLD = 5

class Work(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="work", description="work a shift to earn cores", help="Work a random job to earn 200-900 cores. Jobs pay different amounts. Build a streak by working consecutively — at 5+ streak you earn a 1.5x bonus! 3min cooldown. Check your streak with !streak")
    async def work(self, ctx):
        data = load_bank()
        data = open_account(ctx.author.id, data)
        user_id = str(ctx.author.id)

        data = await debt_prompt(ctx, self.bot, data, ctx.author.id)

        remaining = get_cooldown(ctx.author.id, data, "last_work", COOLDOWN)
        if remaining:
            min_left = round(remaining / 60)
            return await ctx.send(embed=discord.Embed(
                description=f"⧖ cooldown: {min_left}m remaining", color=0xff4500
            ), ephemeral=True)

        is_jackpot = random.random() < JACKPOT_CHANCE
        if is_jackpot:
            job, job_min, job_max = random.choice(JACKPOT_JOBS)
        else:
            job, job_min, job_max = random.choice(JOBS)
        earnings = random.randint(job_min, job_max)

        uid = str(ctx.author.id)
        streak = data[uid].get("work_streak", 0) + 1
        data[uid]["work_streak"] = streak

        streak_bonus = 0
        if streak >= STREAK_THRESHOLD:
            streak_bonus = int(earnings * (STREAK_MULTIPLIER - 1))
            earnings += streak_bonus

        debt_paid, to_wallet = apply_earnings(user_id, data, earnings)
        set_cooldown(ctx.author.id, data, "last_work")
        save_bank(data)

        jackpot_icon = "💎 " if is_jackpot else ""
        desc = f"you worked as a **{job}** and earned {jackpot_icon}**⌬ {earnings:,}** cores"
        if is_jackpot:
            desc += "\n✨ **jackpot!**"
        if streak_bonus:
            desc += f"\n🔥 **streak bonus!** +⌬ {streak_bonus:,} (x{STREAK_MULTIPLIER} streak)"
        if debt_paid:
            desc += f"\n⌬ {debt_paid:,} went toward your debt"

        embed = discord.Embed(title="⚒ shift complete", description=desc, color=0x57f287)
        embed.set_footer(text=f"streak: {streak} · wallet: {data[user_id]['wallet']:,} cores")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="streak", description="check your work streak", help="Shows how many consecutive !work shifts you've completed. At 5+ streak you earn bonus cores.")
    async def streak(self, ctx):
        data = load_bank()
        data = open_account(ctx.author.id, data)
        streak = data[str(ctx.author.id)].get("work_streak", 0)
        emoji = "🔥" if streak >= STREAK_THRESHOLD else "⚒"
        await ctx.send(embed=discord.Embed(
            description=f"{emoji} your work streak: **{streak}**",
            color=0x2b2d31
        ))

async def setup(bot) -> None:
    await bot.add_cog(Work(bot))