import discord
import random
from discord.ext import commands
from helpers.economy_base import load_bank, save_bank, open_account, get_cooldown, set_cooldown, apply_loss, apply_earnings, debt_prompt
from commands.economy.shop import user_has_item
from commands.economy.history import add_tx

ROB_COOLDOWN = 300
BUST_SCENES = [
    "caught in the act", "tripped over your own feet running away",
    "the police were waiting for you", "your getaway car was a bicycle",
    "someone recognized you from the news", "you left your id at the scene",
]

class Rob(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="rob", description="attempt to steal cores from a user's wallet", help="Try to rob another user's wallet. Base 45% success rate — steal up to 25% of their wallet (max 1000). Fail and you pay a fine to your victim. Target must have at least 150 cores. 5min cooldown. Extra Luck (+15% success), Stealthy Shoes (halve fines +10% steal), Invisibility Potion (+5% success).")
    async def rob(self, ctx, member: discord.Member):
        if member.id == ctx.author.id:
            return await ctx.send("⊘ you can't rob yourself!")

        data = load_bank()
        data = open_account(ctx.author.id, data)
        data = open_account(member.id, data)

        data = await debt_prompt(ctx, self.bot, data, ctx.author.id)

        remaining = get_cooldown(ctx.author.id, data, "last_rob", ROB_COOLDOWN)
        if remaining:
            mins = round(remaining / 60, 1)
            return await ctx.send(embed=discord.Embed(
                description=f"⧖ lay low for {mins}m", color=0xff4500
            ), ephemeral=True)

        victim_id = str(member.id)
        robber_id = str(ctx.author.id)

        if data[victim_id]["wallet"] < 150:
            return await ctx.send(embed=discord.Embed(
                description="⊘ this user is too poor to rob. look for someone with at least ⌬ 150 in their wallet.",
                color=0xff4500
            ))

        set_cooldown(ctx.author.id, data, "last_rob")

        has_luck = user_has_item(ctx.author.id, "extra_luck")
        has_stealth = user_has_item(ctx.author.id, "stealthy_shoes")
        has_invis = user_has_item(ctx.author.id, "invisibility_potion")

        success_chance = 0.45
        if has_luck:
            success_chance += 0.15
        if has_invis:
            success_chance += 0.05

        if random.random() < success_chance:
            max_steal = min(1000, int(data[victim_id]["wallet"] * 0.25))
            if has_stealth:
                max_steal = min(1100, int(max_steal * 1.1))
            stolen = random.randint(50, max(50, max_steal))
            data[victim_id]["wallet"] -= stolen
            debt_paid, to_wallet = apply_earnings(robber_id, data, stolen)
            save_bank(data)
            add_tx(ctx.author.id, "earn", stolen, f"robbed {member.name}")
            add_tx(member.id, "loss", -stolen, f"robbed by {ctx.author.name}")
            desc = f"╼ **theft success** ╾\nyou stole **⌬ {stolen:,}** from {member.display_name.lower()}"
            if debt_paid:
                desc += f"\n⌬ {debt_paid:,} went toward your debt"
            embed = discord.Embed(description=desc, color=0x57f287)
        else:
            fine = random.randint(100, 500)
            if has_stealth:
                fine = max(50, fine // 2)
            apply_loss(robber_id, data, fine)
            data[victim_id]["wallet"] += fine
            save_bank(data)
            add_tx(ctx.author.id, "loss", -fine, f"busted robbing {member.name}")
            add_tx(member.id, "earn", fine, f"compensation from {ctx.author.name}")
            debt = data[robber_id]["debt"]
            scene = random.choice(BUST_SCENES)
            desc = f"⊘ **busted!**\n{scene}. fined **⌬ {fine:,}** to {member.display_name.lower()}"
            if debt > 0:
                desc += f"\n⌬ {debt:,} now in debt"
            embed = discord.Embed(description=desc, color=0xff4500)

        if has_invis:
            embed.set_footer(text="no trace left behind")
        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Rob(bot))
