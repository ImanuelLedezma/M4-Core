import discord
import asyncio
import time
from discord.ext import commands
from helpers.time_utils import parse_duration

class Timer(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self._active: dict[int, dict] = {}

    def _fmt(self, s: int) -> str:
        h, r = divmod(s, 3600)
        m, s = divmod(r, 60)
        parts = []
        if h: parts.append(f"`{h}h`")
        if m: parts.append(f"`{m}m`")
        parts.append(f"`{s}s`")
        return " ".join(parts)

    @commands.hybrid_command(name="timer", aliases=["t", "countdown"], description="set a countdown timer", help="Set a countdown timer in the channel. Formats: !timer 30 (seconds), !timer 5m pizza (5 minutes with label), !timer 1h break. Max 24 hours. You'll be pinged and DMed when done. Starting a new timer cancels your previous one.")
    async def timer(self, ctx, duration_or_label: str, *, label_or_none: str = None):
        duration_secs = None
        label = "timer"

        delta = parse_duration(duration_or_label)
        if delta:
            duration_secs = int(delta.total_seconds())
            if label_or_none:
                label = label_or_none
        else:
            try:
                duration_secs = int(duration_or_label)
                if label_or_none:
                    label = label_or_none
            except ValueError:
                return await ctx.send(embed=discord.Embed(
                    description="✖ invalid format. use `!timer 30`, `!timer 5m`, `!timer 1h pizza`",
                    color=0xff4500
                ))

        if duration_secs < 1:
            return await ctx.send(embed=discord.Embed(
                title="✖ invalid duration", description="minimum is `1` second.", color=discord.Color.red()
            ))
        if duration_secs > 86400:
            return await ctx.send(embed=discord.Embed(
                title="✖ too long", description="max duration is `86400` seconds (24h).", color=discord.Color.red()
            ))

        # cancel existing timer
        if ctx.author.id in self._active:
            self._active[ctx.author.id]["task"].cancel()

        embed = discord.Embed(
            title=f"⟳ {label}",
            description=f"time remaining: {self._fmt(duration_secs)}",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"started by {ctx.author.display_name}")
        msg = await ctx.send(embed=embed)

        async def countdown():
            start = time.monotonic()
            update_interval = 5 if duration_secs > 30 else 1
            last_update = -1

            try:
                while True:
                    elapsed = time.monotonic() - start
                    if elapsed >= duration_secs:
                        break
                    remaining = int(duration_secs - elapsed)
                    tick = remaining // update_interval
                    if tick != last_update:
                        last_update = tick
                        embed.description = f"time remaining: {self._fmt(remaining)}"
                        await msg.edit(embed=embed)
                    await asyncio.sleep(0.5)

                done_embed = discord.Embed(
                    title=f"√ {label}",
                    description=f"{ctx.author.mention} your timer is up!",
                    color=discord.Color.green()
                )
                done_embed.set_footer(text=f"started by {ctx.author.display_name}")
                await msg.edit(embed=done_embed)
                await ctx.send(f"{ctx.author.mention} ⏱ **{label}** is done!")

                try:
                    await ctx.author.send(embed=discord.Embed(
                        title=f"⏱ timer done · {label}",
                        description=f"your timer in **{ctx.guild.name}** · #{ctx.channel.name}",
                        color=discord.Color.green()
                    ))
                except discord.Forbidden:
                    pass
            except asyncio.CancelledError:
                embed.description = "⊘ cancelled (replaced by new timer)"
                await msg.edit(embed=embed)
            finally:
                if ctx.author.id in self._active:
                    del self._active[ctx.author.id]

        task = asyncio.create_task(countdown())
        self._active[ctx.author.id] = {
            "task": task,
            "label": label,
            "duration": duration_secs,
            "start": time.monotonic(),
        }

    @commands.hybrid_command(name="timers", aliases=["activetimers", "mytimers"], description="show your active timers", help="Lists all your active countdown timers with labels and time remaining.")
    async def timers_list(self, ctx):
        active = {uid: info for uid, info in self._active.items() if not info["task"].done() and uid == ctx.author.id}
        if not active:
            return await ctx.send(embed=discord.Embed(description="no active timers.", color=0x2b2d31))

        embed = discord.Embed(title=f"⏱ active timers ({len(active)})", color=0x5865f2)
        now = time.monotonic()
        for uid, info in active.items():
            elapsed = now - info["start"]
            remaining = max(0, info["duration"] - int(elapsed))
            embed.add_field(
                name=f"**{info['label']}**",
                value=f"remaining: {self._fmt(remaining)}",
                inline=False,
            )
        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Timer(bot))