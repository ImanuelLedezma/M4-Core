import discord
from discord.ext import commands

class About(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.start_time = discord.utils.utcnow()

    @commands.hybrid_command(name="about", aliases=["botinfo", "bot"], description="show bot information", help="Shows bot version, library, server count, total users, command count, cog count, uptime, latency, developer, and repository link.")
    async def about(self, ctx):
        delta = discord.utils.utcnow() - self.start_time
        hours, rem = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(rem, 60)
        days, hours = divmod(hours, 24)

        parts = []
        if days: parts.append(f"`{days}d`")
        if hours: parts.append(f"`{hours}h`")
        if minutes: parts.append(f"`{minutes}m`")
        parts.append(f"`{seconds}s`")

        cmd_count = len(ctx.bot.commands)
        cog_count = len(ctx.bot.cogs)
        guild_count = len(ctx.bot.guilds)
        user_count = sum(g.member_count or 0 for g in ctx.bot.guilds)
        ping = round(ctx.bot.latency * 1000)

        embed = discord.Embed(
            title="m4-core",
            description="a modular discord bot · economy, moderation, fun & more",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=ctx.bot.user.display_avatar.url)
        embed.add_field(name="library", value="`discord.py`", inline=True)
        embed.add_field(name="servers", value=f"`{guild_count}`", inline=True)
        embed.add_field(name="users", value=f"`{user_count:,}`", inline=True)
        embed.add_field(name="commands", value=f"`{cmd_count}`", inline=True)
        embed.add_field(name="cogs", value=f"`{cog_count}`", inline=True)
        embed.add_field(name="uptime", value=" ".join(parts), inline=True)
        embed.add_field(name="latency", value=f"`{ping}ms`", inline=True)
        embed.add_field(name="developer", value="immie & nyx", inline=True)
        embed.add_field(name="repository", value="[github](https://github.com/immie/m4-core)", inline=True)
        embed.set_footer(text=f"m4-core v1 · {discord.__version__}")
        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(About(bot))