import discord
import random
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType
from helpers.database import dumbass_increment, dumbass_leaderboard

REASONS = [
    "microwaved a fork",
    "googled 'google'",
    "sent a text to the wrong person and didn't realize it",
    "tried to reply to a voicemail",
    "locked themselves out of their own house twice in one day",
    "asked what time 12pm is",
    "tried to use a computer without a mouse",
    "argued with autocorrect and lost",
    "put the milk in the cupboard",
    "sent a screenshot of a text instead of forwarding it",
    "spent 10 minutes looking for their phone while on a call",
    "clicked 'forgot password' three times in a row",
    "tried to zoom in on a physical piece of paper",
    "said 'you too' when a waiter said enjoy your meal, then said it again",
    "walked into a push door",
    "got into the passenger seat of their own car",
    "tripped over nothing and blamed the floor",
    "replied all on a company-wide email",
    "accidentally sent a meme in a professional chat",
    "used the wrong emoji in a message and didn't know how to react",
    "tried to unlock their phone with their face while wearing sunglasses",
    "forgot how to spell a common word and had to look it up",
    "laughed at a joke they didn't understand and then had to pretend they got it",
    "started a sentence and then forgot what they were going to say",
    "set two alarms 1 minute apart instead of snoozing",
    "put their phone in the fridge and looked for it for 20 minutes",
    "tried to push a pull door for 30 seconds before giving up",
]

RANKS = [
    ("bronze", 0), ("silver", 3), ("gold", 6), ("platinum", 10),
    ("diamond", 15), ("legendary", 20), ("cosmic", 30), ("titan", 50),
]

SEALS = ["🔏 certified", "📜 notarized", "⚖ legally binding", "🏛 government approved", "👁 witnessed"]

class Dumbass(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    def _get_rank(self, count: int) -> str:
        rank = "bronze"
        for name, threshold in reversed(RANKS):
            if count >= threshold:
                rank = name
                break
        return rank

    @commands.hybrid_command(name="dumbass", aliases=["certified", "cert"], description="issue a certificate of dumbass", help="Issue a certificate of dumbass to yourself or someone else. Tracks certifications per user with tiers: bronze, silver, gold, platinum, diamond, legendary, cosmic, titan.")
    @cooldown(1, 5, BucketType.user)
    async def dumbass(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        count = dumbass_increment(ctx.guild.id, target.id)
        rank = self._get_rank(count)
        reason = random.choice(REASONS)
        seal = random.choice(SEALS)
        number = random.randint(10000, 99999)
        date = discord.utils.utcnow().strftime("%B %d, %Y")

        embed = discord.Embed(
            title="certificate of dumbass",
            color=0xf1c40f
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.description = (
            f"*this is to certify that*\n"
            f"## {target.display_name}\n"
            f"*has been officially recognized as a certified dumbass*"
        )
        embed.add_field(name="reason", value=reason, inline=False)
        embed.add_field(name="rank", value=f"`{rank} tier`", inline=True)
        embed.add_field(name="times certified", value=f"`{count}`", inline=True)
        embed.add_field(name="certificate no.", value=f"`#{number}`", inline=True)
        embed.add_field(name="issued", value=date, inline=True)
        embed.set_footer(text=f"{seal} · issued by {ctx.author.display_name}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="dumbasslb", aliases=["dblb", "dumbassleaderboard"], description="show the dumbass leaderboard", help="Shows the top 10 most certified dumbasses in the server with medal rankings.")
    async def dumbass_leaderboard(self, ctx):
        top = dumbass_leaderboard(ctx.guild.id)
        if not top:
            return await ctx.send(embed=discord.Embed(
                description="no dumbass certifications in this server yet.",
                color=0x2b2d31
            ))

        embed = discord.Embed(title="🏆 dumbass leaderboard", color=0xf1c40f)
        medals = ["🥇", "🥈", "🥉"]

        for i, entry in enumerate(top):
            member = ctx.guild.get_member(entry["user_id"])
            name = member.display_name if member else "unknown"
            prefix = medals[i] if i < 3 else f"`{i+1}.`"
            embed.add_field(
                name=f"{prefix} {name}",
                value=f"`{entry['count']}` certifications · {self._get_rank(entry['count'])} tier",
                inline=False
            )

        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Dumbass(bot))
