import discord
import random
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType
from helpers.storage import load, save

CHOICES = ["rock", "paper", "scissors"]
BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
ICONS = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
RPS_FILE = "rps.msgpack"

class Rps(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    def _load_scores(self) -> dict:
        return load(RPS_FILE)

    def _save_scores(self, data: dict) -> None:
        save(RPS_FILE, data)

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
        scores = self._load_scores()
        uid = str(ctx.author.id)
        stats = scores.get(uid, {"wins": 0, "losses": 0, "ties": 0})

        if choice == bot_choice:
            result = "tie"
            color = discord.Color.yellow()
            stats["ties"] += 1
        elif BEATS[choice] == bot_choice:
            result = "you win!"
            color = discord.Color.green()
            stats["wins"] += 1
        else:
            result = "you lose.."
            color = discord.Color.red()
            stats["losses"] += 1

        scores[uid] = stats
        self._save_scores(scores)

        total = stats["wins"] + stats["losses"] + stats["ties"]
        record = f"{stats['wins']}w/{stats['losses']}l/{stats['ties']}t"

        embed = discord.Embed(title="rock paper scissors", color=color)
        embed.add_field(name="you", value=f"{ICONS[choice]} {choice}", inline=True)
        embed.add_field(name="bot", value=f"{ICONS[bot_choice]} {bot_choice}", inline=True)
        embed.add_field(name="result", value=result, inline=False)
        embed.set_footer(text=f"record: {record} ({total} games)")
        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Rps(bot))