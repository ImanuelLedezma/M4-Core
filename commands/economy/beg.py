import discord
import random
from discord.ext import commands
from helpers.economy_base import load_bank, save_bank, open_account, get_cooldown, set_cooldown, apply_earnings, debt_prompt

COOLDOWN = 120

SUCCESS_SCENES = [
    ("a stranger tossed you", 10, 40),
    ("you found", 15, 50),
    ("someone tipped you", 20, 60),
    ("a friend spotted you", 30, 70),
    ("a kind soul donated", 25, 85),
    ("you panhandled and got", 15, 45),
    ("someone gave you their spare change:", 10, 35),
]

FAIL_SCENES = [
    "no one gave you any money",
    "someone laughed in your face",
    "a security guard told you to move along",
    "you got ignored by everyone",
    "someone pretended not to see you",
    "a street performer outsold you",
]

class Beg(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="beg", description="request spare cores", help="Beg for cores from strangers. 70% success rate for 10-85 cores. 2min cooldown. Various success and failure scenes add flavor.")
    async def beg(self, ctx):
        data = load_bank()
        data = open_account(ctx.author.id, data)
        user_id = str(ctx.author.id)

        data = await debt_prompt(ctx, self.bot, data, ctx.author.id)

        remaining = get_cooldown(ctx.author.id, data, "last_beg", COOLDOWN)
        if remaining:
            return await ctx.send(embed=discord.Embed(
                description=f"⧖ retry in {remaining}s", color=0xff4500
            ), ephemeral=True)

        set_cooldown(ctx.author.id, data, "last_beg")

        if random.random() < 0.3:
            scene = random.choice(FAIL_SCENES)
            return await ctx.send(embed=discord.Embed(
                description=f"⊘ {scene}", color=0xfee75c
            ))

        scene, min_coins, max_coins = random.choice(SUCCESS_SCENES)
        earnings = random.randint(min_coins, max_coins)
        debt_paid, _ = apply_earnings(user_id, data, earnings)
        save_bank(data)

        desc = f"◈ {scene} **⌬ {earnings}** cores"
        if debt_paid:
            desc += f"\n⌬ {debt_paid:,} went toward your debt"

        embed = discord.Embed(description=desc, color=0xfee75c)
        embed.set_footer(text=f"wallet: {data[user_id]['wallet']:,} cores")
        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Beg(bot))