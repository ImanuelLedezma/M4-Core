import discord
import asyncio
import time
from discord.ext import commands
from helpers.time_utils import parse_duration_with_label

class Remind(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self._reminders: dict[int, list[dict]] = {}

    @commands.hybrid_command(name="remind", aliases=["reminder"], description="set a reminder", help="Set a DM reminder. Formats: !remind 10s, !remind 5m pizza, !remind 1h deploy. Max 7 days. You'll be DMed when the time is up.")
    async def remind(self, ctx, duration: str, *, message: str):
        parsed = parse_duration_with_label(duration)
        if not parsed:
            return await ctx.send(embed=discord.Embed(
                description="⊘ invalid duration. use `10s`, `5m`, `2h`, `1d`.",
                color=0xff4500
            ))

        seconds, label = parsed
        if seconds > 86400 * 7:
            return await ctx.send(embed=discord.Embed(
                description="⊘ max reminder duration is 7 days.",
                color=0xff4500
            ))

        uid = ctx.author.id
        entry = {
            "message": message,
            "channel": ctx.channel.name,
            "guild": ctx.guild.name,
            "ends_at": time.time() + seconds,
        }
        if uid not in self._reminders:
            self._reminders[uid] = []
        self._reminders[uid].append(entry)

        await ctx.send(embed=discord.Embed(
            description=f"√ i'll remind you about **{message}** in **{label}**.",
            color=0x2b2d31
        ))

        asyncio.create_task(self._notify(ctx, uid, entry, seconds))

    @commands.hybrid_command(name="reminders", aliases=["listreminders"], description="show your active reminders", help="Lists all your active reminders with time remaining and message.")
    async def reminders(self, ctx):
        uid = ctx.author.id
        active = self._reminders.get(uid, [])
        if not active:
            return await ctx.send(embed=discord.Embed(description="no active reminders.", color=0x2b2d31))

        embed = discord.Embed(title=f"⏱ reminders ({len(active)})", color=0x5865f2)
        now = time.time()
        for r in active:
            remaining = int(r["ends_at"] - now)
            if remaining < 0:
                continue
            h, rem = divmod(remaining, 3600)
            m, s = divmod(rem, 60)
            parts = []
            if h: parts.append(f"{h}h")
            if m: parts.append(f"{m}m")
            parts.append(f"{s}s")
            embed.add_field(
                name=f"in {' '.join(parts)}",
                value=f"**{r['message'][:100]}** — #{r['channel']}",
                inline=False
            )
        await ctx.send(embed=embed)

    async def _notify(self, ctx, uid: int, entry: dict, seconds: int):
        try:
            await asyncio.sleep(seconds)

            if uid in self._reminders and entry in self._reminders[uid]:
                self._reminders[uid].remove(entry)

            try:
                await ctx.author.send(embed=discord.Embed(
                    title="⏱ reminder",
                    description=entry["message"],
                    color=0x5865f2
                ).set_footer(text=f"set in #{entry['channel']} · {entry['guild']}"))
            except discord.Forbidden:
                await ctx.send(embed=discord.Embed(
                    description=f"{ctx.author.mention} ⏱ reminder: **{entry['message']}**",
                    color=0x5865f2
                ))
        except Exception:
            pass

async def setup(bot) -> None:
    await bot.add_cog(Remind(bot))