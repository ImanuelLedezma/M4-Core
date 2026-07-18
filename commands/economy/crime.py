import discord
import random
from discord.ext import commands
from helpers.economy_base import load_bank, save_bank, open_account, get_cooldown, set_cooldown, apply_loss, apply_earnings, debt_prompt
from commands.economy.shop import user_has_item

CRIME_COOLDOWN = 600

CRIMES = [
    "hacked a government server", "pickpocketed a tourist", "sold knockoff merch",
    "ran a pyramid scheme", "shoplifted a vending machine", "forged a document",
    "jaywalked aggressively", "smuggled rare cheese", "stole a car and returned it with a full tank",
    "illegally downloaded a movie", "vandalized a public statue", "committed tax fraud",
    "hacked into a casino and won big", "stole a bike and used it for a day before returning it",
    "ran an illegal lemonade stand", "counterfeited trading cards", "sold your sibling's belongings",
    "scammed a bot into buying nothing", "ran a gambling ring for pigeons",
]

BUST_SCENES = [
    "caught in the act", "tripped over your own feet running away",
    "the police were waiting for you", "your getaway car was a bicycle",
    "someone recognized you from the news", "you left your id at the scene",
]

class Crime(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="crime", description="commit a crime for cores", help="Commit a random crime to earn 200-900 cores. 40% chance of getting caught — pay a fine of 100-600 cores. 10min cooldown. Items: Extra Luck (+15%, +10% earnings), Donut (halve fines), Fake License (-1min cd), Invisibility Potion (+5%, no log).")
    async def crime(self, ctx):
        data = load_bank()
        data = open_account(ctx.author.id, data)
        user_id = str(ctx.author.id)

        data = await debt_prompt(ctx, self.bot, data, ctx.author.id)

        has_license = user_has_item(ctx.author.id, "fake_license")
        cd = CRIME_COOLDOWN - 60 if has_license else CRIME_COOLDOWN
        remaining = get_cooldown(ctx.author.id, data, "last_crime", cd)
        if remaining:
            mins = round(remaining / 60)
            return await ctx.send(embed=discord.Embed(
                description=f"⧖ lay low for {mins}m", color=0xff4500
            ), ephemeral=True)

        set_cooldown(ctx.author.id, data, "last_crime")

        has_luck = user_has_item(ctx.author.id, "extra_luck")
        has_donut = user_has_item(ctx.author.id, "donut")
        has_invis = user_has_item(ctx.author.id, "invisibility_potion")

        success_chance = 0.6
        if has_luck:
            success_chance += 0.15
        if has_invis:
            success_chance += 0.05

        if random.random() < success_chance:
            earnings = random.randint(200, 900)
            if has_luck:
                earnings = int(earnings * 1.1)
            debt_paid, _ = apply_earnings(user_id, data, earnings)
            save_bank(data)
            act = random.choice(CRIMES)
            desc = f"╼ **crime pays** ╾\nyou {act} and earned **⌬ {earnings:,}** cores"
            if debt_paid:
                desc += f"\n⌬ {debt_paid:,} went toward your debt"
            embed = discord.Embed(description=desc, color=0x57f287)
        else:
            fine = random.randint(100, 600)
            if has_donut:
                fine = max(50, fine // 2)
            apply_loss(user_id, data, fine)
            save_bank(data)
            debt = data[user_id]["debt"]
            scene = random.choice(BUST_SCENES)
            desc = f"⊘ **busted!**\n{scene}. fined **⌬ {fine:,}** cores"
            if debt > 0:
                desc += f"\n⌬ {debt:,} now in debt"
            embed = discord.Embed(description=desc, color=0xff4500)

        embed.set_footer(text=f"wallet: {data[user_id]['wallet']:,} cores")
        if has_invis:
            embed.set_footer(text=f"wallet: {data[user_id]['wallet']:,} cores · no trace left behind")
        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Crime(bot))