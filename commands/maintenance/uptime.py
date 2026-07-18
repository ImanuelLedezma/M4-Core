import discord
from discord.ext import commands

class Uptime(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.start_time = discord.utils.utcnow()

    @commands.hybrid_command(name="uptime", description="show bot runtime and memory usage", help="Shows bot uptime, WebSocket latency, memory usage (MB), and CPU usage. Memory/CPU requires psutil library (optional).")
    async def uptime(self, ctx):
        delta = discord.utils.utcnow() - self.start_time
        hours, rem = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(rem, 60)
        days, hours = divmod(hours, 24)

        parts = []
        if days: parts.append(f"`{days}d`")
        if hours: parts.append(f"`{hours}h`")
        if minutes: parts.append(f"`{minutes}m`")
        parts.append(f"`{seconds}s`")

        try:
            import psutil
            proc = psutil.Process()
            mem = proc.memory_info().rss / 1024 / 1024
            cpu = proc.cpu_percent(interval=0.1)
            mem_str = f"`{mem:.1f}mb`"
            cpu_str = f"`{cpu:.1f}%`"
        except ImportError:
            mem_str = "`n/a`"
            cpu_str = "`n/a`"

        embed = discord.Embed(
            title="⟳ system info",
            color=discord.Color.blue()
        )
        embed.add_field(name="uptime", value=" ".join(parts), inline=True)
        embed.add_field(name="latency", value=f"`{round(self.bot.latency * 1000)}ms`", inline=True)
        embed.add_field(name="memory", value=mem_str, inline=True)
        embed.add_field(name="cpu", value=cpu_str, inline=True)
        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Uptime(bot))