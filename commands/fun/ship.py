import discord
import random
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType

BAR_FILLED = "█"
BAR_EMPTY = "░"

EMOJI_METER = [
    ("💔", "absolutely not."),
    ("❤️‍🩹", "it's a stretch..."),
    ("💛", "maybe something there?"),
    ("💚", "pretty good match!"),
    ("💖", "soulmates!"),
]

SHIP_NAMES = [
    lambda a, b: f"{a[:len(a)//2]}{b[len(b)//2:]}",
    lambda a, b: f"{a[:3]}{b[-3:]}",
    lambda a, b: f"{b[:3]}×{a[-3:]}",
    lambda a, b: f"{a}·{b}",
]

class Ship(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    def _ship_name(self, name1: str, name2: str) -> str:
        return random.choice(SHIP_NAMES)(name1.lower(), name2.lower())

    @commands.hybrid_command(name="ship", description="check compatibility between two users", help="Check romantic compatibility between two users. Shows a percentage, visual bar, emoji verdict, and generates a ship name. If only one user is given, ships them with you.")
    @cooldown(1, 5, BucketType.user)
    async def ship(self, ctx, member1: discord.Member, member2: discord.Member = None):
        if member2 is None:
            member2 = ctx.author

        score = random.randint(0, 100)
        filled = score // 10
        bar = BAR_FILLED * filled + BAR_EMPTY * (10 - filled)

        idx = min(score // 25, len(EMOJI_METER) - 1)
        emoji, verdict = EMOJI_METER[idx]

        sname = self._ship_name(member1.display_name, member2.display_name)

        embed = discord.Embed(
            title=f"{emoji} ship · {sname}",
            color=0x5865f2
        )
        embed.description = f"{member1.mention} × {member2.mention}"
        embed.add_field(name="compatibility", value=f"`{bar}` **{score}%**", inline=False)
        embed.add_field(name="verdict", value=f"{emoji} {verdict}", inline=False)
        embed.set_thumbnail(url=member1.display_avatar.url)
        embed.set_footer(text=f"requested by {ctx.author.display_name}")

        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Ship(bot))