import discord
from datetime import timedelta
from discord.ext import commands
from helpers.storage import load, save

WARNINGS_FILE = "warnings.msgpack"
AUTO_TIMEOUT_THRESHOLD = 5

def load_warnings():
    return load(WARNINGS_FILE)

def save_warnings(data):
    save(WARNINGS_FILE, data)

class Warn(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="warn", description="issue a warning to a member", help="Issue a warning to a member. DMs the user. At 5 warnings, the user is automatically timed out for 1 hour. Requires Moderate Members permission.")
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = "no reason provided"):
        if member == ctx.author:
            return await ctx.send(embed=discord.Embed(
                title="✖ invalid target", description="you can't warn yourself.", color=discord.Color.red()
            ))
        if member.top_role >= ctx.author.top_role:
            return await ctx.send(embed=discord.Embed(
                title="✖ insufficient hierarchy",
                description="you can't warn someone with an equal or higher role.",
                color=discord.Color.red()
            ))

        data = load_warnings()
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        if guild_id not in data:
            data[guild_id] = {}
        if user_id not in data[guild_id]:
            data[guild_id][user_id] = []

        data[guild_id][user_id].append({
            "reason": reason,
            "by": str(ctx.author.id),
            "at": ctx.message.created_at.isoformat(),
        })
        save_warnings(data)

        count = len(data[guild_id][user_id])

        try:
            await member.send(embed=discord.Embed(
                title=f"⚠ warning in {ctx.guild.name}",
                description=f"**reason:** {reason}\n**warned by:** {ctx.author.name}\n**total warnings:** `{count}`",
                color=discord.Color.yellow()
            ))
        except discord.Forbidden:
            pass

        await ctx.send(embed=discord.Embed(
            title="√ warned",
            description=f"warned {member.mention} · **{reason}**\ntotal warnings: `{count}`",
            color=discord.Color.green()
        ))

        if count >= AUTO_TIMEOUT_THRESHOLD and ctx.guild.me.guild_permissions.moderate_members:
            delta = discord.utils.utcnow() + timedelta(hours=1)
            await member.timeout(delta, reason=f"auto-timeout: reached {count} warnings")
            await ctx.send(embed=discord.Embed(
                description=f"⊘ {member.mention} auto-timed out for 1h (threshold: {AUTO_TIMEOUT_THRESHOLD} warnings)",
                color=0xff4500
            ))

    @commands.hybrid_command(name="warnings", aliases=["warnlist"], description="view a member's warnings", help="Shows all warnings for a member with reason, who issued it, and date. Requires Moderate Members permission.")
    @commands.has_permissions(moderate_members=True)
    async def warnings(self, ctx, member: discord.Member):
        data = load_warnings()
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        warns = data.get(guild_id, {}).get(user_id, [])

        if not warns:
            return await ctx.send(embed=discord.Embed(
                title="warnings",
                description=f"{member.mention} has no warnings.",
                color=discord.Color.blue()
            ))

        embed = discord.Embed(
            title=f"warnings · {member.name}",
            description=f"total: `{len(warns)}`",
            color=discord.Color.yellow()
        )

        for i, w in enumerate(warns, 1):
            embed.add_field(
                name=f"#{i} · {w['at'][:10]}",
                value=f"**reason:** {w['reason']}\n**by:** <@{w['by']}>",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="rmwarn", aliases=["delwarn", "removewarn"], description="remove a warning by index", help="Remove a specific warning by its index number. Use !warnings to see warning indices. Requires Moderate Members permission.")
    @commands.has_permissions(moderate_members=True)
    async def rmwarn(self, ctx, member: discord.Member, index: int):
        data = load_warnings()
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        warns = data.get(guild_id, {}).get(user_id, [])

        if not warns:
            return await ctx.send(embed=discord.Embed(
                title="✖ no warnings",
                description=f"{member.mention} has no warnings.",
                color=discord.Color.red()
            ))

        if index < 1 or index > len(warns):
            return await ctx.send(embed=discord.Embed(
                title="✖ invalid index",
                description=f"provide a number between `1` and `{len(warns)}`.",
                color=discord.Color.red()
            ))

        removed = data[guild_id][user_id].pop(index - 1)
        save_warnings(data)

        await ctx.send(embed=discord.Embed(
            title="√ warning removed",
            description=f"removed warning `#{index}` from {member.mention}\n**reason was:** {removed['reason']}",
            color=discord.Color.green()
        ))

    @commands.hybrid_command(name="clearwarns", aliases=["clearwarnings", "resetwarns"], description="clear all warnings for a member", help="Delete ALL warnings for a member. No undo. Requires Moderate Members permission.")
    @commands.has_permissions(moderate_members=True)
    async def clearwarns(self, ctx, member: discord.Member):
        data = load_warnings()
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        if guild_id in data and user_id in data[guild_id]:
            del data[guild_id][user_id]
            save_warnings(data)

        await ctx.send(embed=discord.Embed(
            description=f"√ cleared all warnings for {member.mention}.",
            color=discord.Color.green()
        ))

async def setup(bot) -> None:
    await bot.add_cog(Warn(bot))