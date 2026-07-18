import asyncio
import discord
import random
import time
from discord.ext import commands
from helpers.database import level_get, level_update

XP_MIN = 15
XP_MAX = 25
XP_COOLDOWN = 60
LEVEL_BASE = 100
LEVEL_FACTOR = 1.5

def xp_for_level(lvl: int) -> int:
    return int(LEVEL_BASE * (lvl ** LEVEL_FACTOR))

def level_from_xp(xp: int) -> int:
    return max(1, int((xp / LEVEL_BASE) ** (1 / LEVEL_FACTOR)))

class Levels(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self._cooldowns: dict[int, float] = {}
        self._channel_id: int | None = None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        if self._channel_id and message.channel.id != self._channel_id:
            return

        now = time.time()
        if message.author.id in self._cooldowns:
            if now - self._cooldowns[message.author.id] < XP_COOLDOWN:
                return

        self._cooldowns[message.author.id] = now

        xp_gain = random.randint(XP_MIN, XP_MAX)
        stats = level_get(message.author.id)
        new_xp = stats["xp"] + xp_gain
        new_level = level_from_xp(new_xp)
        leveled_up = new_level > stats["level"]

        level_update(message.author.id, xp_gain, new_level)

        if leveled_up:
            try:
                await message.channel.send(embed=discord.Embed(
                    title=f"√ level up!",
                    description=f"{message.author.mention} reached **level {new_level}**",
                    color=0x57f287
                ))
            except (discord.Forbidden, discord.NotFound):
                pass

    @commands.hybrid_command(name="rank", description="check your level and xp", help="Shows your current level, XP progress, and XP needed for the next level.")
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        stats = level_get(member.id)
        xp = stats["xp"]
        lvl = stats["level"]
        next_xp = xp_for_level(lvl + 1)
        prog = min(1.0, xp / next_xp) if next_xp else 1.0
        bar_len = 12
        filled = int(prog * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)

        embed = discord.Embed(title=f"◈ {member.display_name}'s rank", color=0x2b2d31)
        embed.add_field(name="level", value=str(lvl), inline=True)
        embed.add_field(name="xp", value=f"{xp:,} / {next_xp:,}", inline=True)
        embed.add_field(name="progress", value=f"`[{bar}]`", inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="setlevelchannel", description="set the channel for level-up announcements", help="Set the channel where level-up messages are posted. Requires Manage Guild permission.")
    @commands.has_permissions(manage_guild=True)
    async def set_channel(self, ctx, channel: discord.TextChannel):
        self._channel_id = channel.id
        await ctx.send(embed=discord.Embed(
            description=f"√ level-up channel set to {channel.mention}", color=0x57f287
        ))

async def setup(bot) -> None:
    await bot.add_cog(Levels(bot))
