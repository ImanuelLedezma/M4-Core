import discord
import random
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType

RESPONSES = [
    "it is certain.", "without a doubt.", "yes, definitely.",
    "you may rely on it.", "most likely.", "outlook good.",
    "signs point to yes.", "reply hazy, try again.", "ask again later.",
    "cannot predict now.", "don't count on it.", "my sources say no.",
    "outlook not so good.", "very doubtful.", "absolutely not.",
    "the stars say yes.", "the universe is uncertain.", "i wouldn't bet on it.",
    "it is decidedly so.", "my reply is no.", "better not tell you now.",
]

GIFS = [
    "https://media.tenor.com/7ES5Z1cJwBkAAAAj/8ball-magic-8-ball.gif",
    "https://media.tenor.com/3J3V5Qn9QqYAAAAi/magic-8-ball-eight-ball.gif",
]

class EightBall(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="8ball", aliases=["ask"], description="ask the magic 8ball a question", help="Ask the magic 8ball a yes/no question and receive a cryptic answer.")
    @cooldown(1, 5, BucketType.user)
    async def eightball(self, ctx, *, question: str):
        embed = discord.Embed(title="⊙ 8ball", color=0x5865f2)
        embed.add_field(name="question", value=question, inline=False)
        embed.add_field(name="answer", value=f"🎱 **{random.choice(RESPONSES)}**", inline=False)
        embed.set_thumbnail(url=random.choice(GIFS))
        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(EightBall(bot))