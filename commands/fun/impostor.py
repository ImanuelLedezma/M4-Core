import discord
import random
import asyncio
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType

ALWAYS_SUS = {"nyxgoober"}
SUS_COLORS = {"red", "dark red", "maroon", "crimson", "brown", "orange red"}

VERDICTS_SUS = [
    "extremely suspicious. do not trust",
    "something is very off here",
    "the scan doesn't lie, very sus",
    "anomalous readings detected",
    "trust level: zero",
    "impostor detected. eject immediately",
]

VERDICTS_CLEAR = [
    "probably fine. probably",
    "no anomalies detected",
    "seems legit. for now.",
    "cleared, but stay alert",
    "scan complete, nothing unusual",
]

SCAN_STEPS = [
    "⟳ initializing biometric scan...",
    "⟳ cross-referencing identity matrix...",
    "⟳ analyzing behavioral patterns...",
    "⟳ checking timeline inconsistencies...",
    "⟳ running anomaly detection...",
    "⟳ scanning memory banks...",
    "⟳ verifying neural signature...",
    "⟳ finalizing report...",
]

class Impostor(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="impostor", aliases=["sus", "scan"], description="scan a user for imposter activity", help="Run an 8-step impostor scan on a user. Detects sus activity based on name, color, and random factors.")
    @cooldown(1, 5, BucketType.user)
    async def impostor(self, ctx, member: discord.Member = None):
        target = member or ctx.author

        embed = discord.Embed(
            title="⌖ scanning",
            description=SCAN_STEPS[0],
            color=0x5865f2
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        msg = await ctx.send(embed=embed)

        for step in SCAN_STEPS[1:]:
            await asyncio.sleep(0.9)
            embed.description = step
            await msg.edit(embed=embed)

        await asyncio.sleep(0.8)

        is_sus = target.name.lower() in ALWAYS_SUS
        if not is_sus:
            try:
                r, g, b = target.color.to_rgb()
                if r > 150 and r > g * 1.5 and r > b * 1.5:
                    is_sus = True
            except Exception:
                pass
        if not is_sus:
            is_sus = random.random() < 0.35

        sus_score = random.randint(82, 99) if is_sus else random.randint(3, 35)
        verdict = random.choice(VERDICTS_SUS if is_sus else VERDICTS_CLEAR)
        bar = "█" * (sus_score // 10) + "░" * (10 - sus_score // 10)

        result_embed = discord.Embed(
            title=f"{'⚠ impostor detected' if is_sus else '√ scan complete'}",
            color=0xff4500 if is_sus else 0x57f287
        )
        result_embed.set_thumbnail(url=target.display_avatar.url)
        result_embed.add_field(name="subject", value=target.mention, inline=True)
        result_embed.add_field(name="sus level", value=f"`{bar}` {sus_score}%", inline=False)
        result_embed.add_field(name="verdict", value=verdict, inline=False)
        result_embed.set_footer(text="scan powered by m4-core anomaly engine")
        await msg.edit(embed=result_embed)

async def setup(bot) -> None:
    await bot.add_cog(Impostor(bot))