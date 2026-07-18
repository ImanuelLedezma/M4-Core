import discord
import random
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType
from helpers.database import rps_get, rps_update

CHOICES = ["rock", "paper", "scissors"]
BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
ICONS = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}

class Rps(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="rps", description="play rock paper scissors", help="Play rock paper scissors against the bot. Tracks your wins, losses, and ties permanently.")
    @cooldown(1, 3, BucketType.user)
    async def rps(self, ctx, choice: str):
        choice = choice.lower()
        if choice not in CHOICES:
            return await ctx.send(embed=discord.Embed(
                title="✖ invalid choice",
                description="choose `rock`, `paper`, or `scissors`.",
                color=discord.Color.red()
            ))

        bot_choice = random.choice(CHOICES)
        stats = rps_get(ctx.author.id)

        if choice == bot_choice:
            result = "tie"
            color = discord.Color.yellow()
            rps_update(ctx.author.id, ties=1)
        elif BEATS[choice] == bot_choice:
            result = "you win!"
            color = discord.Color.green()
            rps_update(ctx.author.id, wins=1)
        else:
            result = "you lose.."
            color = discord.Color.red()
            rps_update(ctx.author.id, losses=1)

        total = stats["wins"] + stats["losses"] + stats["ties"]
        new_stats = rps_get(ctx.author.id)
        record = f"{new_stats['wins']}w/{new_stats['losses']}l/{new_stats['ties']}t"

        embed = discord.Embed(title="rock paper scissors", color=color)
        embed.add_field(name="you", value=f"{ICONS[choice]} {choice}", inline=True)
        embed.add_field(name="bot", value=f"{ICONS[bot_choice]} {bot_choice}", inline=True)
        embed.add_field(name="result", value=result, inline=False)
        embed.set_footer(text=f"record: {record} ({total} games)")
        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Rps(bot))
