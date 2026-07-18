import asyncio
import discord
import random
import time
from discord.ext import commands
from helpers.storage import load, save

XP_FILE = "levels.msgpack"
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

    async def _load(self) -> dict:
        return await asyncio.to_thread(load, XP_FILE)

    async def _save(self, data: dict) -> None:
        await asyncio.to_thread(save, XP_FILE, data)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        now = time.time()
        if message.author.id in self._cooldowns:
            if now - self._cooldowns[message.author.id] < XP_COOLDOWN:
                return
        self._cooldowns[message.author.id] = now

        data = await self._load()
        gid = str(message.guild.id)
        uid = str(message.author.id)

        if gid not in data:
            data[gid] = {}

        old_xp = data[gid].get(uid, 0)
        old_level = level_from_xp(old_xp)
        earned = random.randint(XP_MIN, XP_MAX)
        data[gid][uid] = old_xp + earned
        new_level = level_from_xp(data[gid][uid])
        await self._save(data)

        if new_level > old_level:
            if self._channel_id:
                ch = self.bot.get_channel(self._channel_id)
                if ch:
                    await ch.send(embed=discord.Embed(
                        description=f"🎉 {message.author.mention} leveled up to **level {new_level}**!",
                        color=0x57f287
                    ))
                else:
                    await message.channel.send(embed=discord.Embed(
                        description=f"🎉 {message.author.mention} leveled up to **level {new_level}**!",
                        color=0x57f287
                    ))

    @commands.hybrid_command(name="rank", aliases=["level", "xp"], description="check your level and XP", help="Shows your current level, XP, and progress toward the next level for this server.")
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        data = await self._load()
        gid = str(ctx.guild.id)
        uid = str(member.id)

        xp = data.get(gid, {}).get(uid, 0)
        lvl = level_from_xp(xp)
        current = xp_for_level(lvl)
        next_xp = xp_for_level(lvl + 1)
        progress = xp - current
        needed = next_xp - current
        pct = min(100, int(progress / needed * 100)) if needed else 0
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)

        embed = discord.Embed(
            title=f"🎮 {member.display_name}",
            color=member.color if member.color.value else 0x5865f2
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="level", value=f"`{lvl}`", inline=True)
        embed.add_field(name="total XP", value=f"`{xp:,}`", inline=True)
        embed.add_field(name="progress", value=f"`{bar}` **{xp - current:,}** / **{needed:,}** XP", inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="lblevel", aliases=["leaderboardlevel", "lvl"], description="show the level leaderboard", help="Shows the top 10 highest-level users in this server.")
    async def level_leaderboard(self, ctx):
        data = await self._load()
        gid = str(ctx.guild.id)
        guild_data = data.get(gid, {})
        if not guild_data:
            return await ctx.send(embed=discord.Embed(description="no level data yet in this server.", color=0x2b2d31))

        sorted_users = sorted(guild_data.items(), key=lambda x: x[1], reverse=True)[:10]
        embed = discord.Embed(title="🏆 level leaderboard", color=0xf1c40f)
        medals = ["🥇", "🥈", "🥉"]

        for i, (uid, xp) in enumerate(sorted_users):
            member = ctx.guild.get_member(int(uid))
            name = member.display_name if member else "unknown"
            lvl = level_from_xp(xp)
            prefix = medals[i] if i < 3 else f"`{i+1}.`"
            embed.add_field(
                name=f"{prefix} {name}",
                value=f"level `{lvl}` · {xp:,} XP",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="setlevelchannel", description="set channel for level-up announcements", help="Set the channel where level-up messages are posted. Requires Manage Guild permission.")
    @commands.has_permissions(manage_guild=True)
    async def set_level_channel(self, ctx, channel: discord.TextChannel):
        self._channel_id = channel.id
        await ctx.send(embed=discord.Embed(
            description=f"√ level-up announcements set to {channel.mention}",
            color=0x57f287
        ))

async def setup(bot) -> None:
    await bot.add_cog(Levels(bot))