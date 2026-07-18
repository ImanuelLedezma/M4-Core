import discord
from discord.ext import commands

PRESETS = {
    "off": 0,
    "slow": 5,
    "medium": 15,
    "fast": 30,
    "very slow": 60,
    "extreme": 300,
    "1h": 3600,
    "6h": 21600,
}

class Slowmode(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="slowmode", aliases=["sm"], description="set channel slowmode", help="Set the channel slowmode delay. Use a number (0-21600 seconds) or a preset: off, slow (5s), medium (15s), fast (30s), very slow (60s), extreme (5min). Use !sm presets to see all options. Requires Manage Channels permission.")
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, value: str):
        if value.lower() == "presets":
            desc = "\n".join(f"`{k}`" for k in PRESETS)
            return await ctx.send(embed=discord.Embed(
                title="slowmode presets",
                description=desc,
                color=0x2b2d31
            ))

        if value.lower() in PRESETS:
            seconds = PRESETS[value.lower()]
        else:
            try:
                seconds = int(value)
            except ValueError:
                return await ctx.send(embed=discord.Embed(
                    description="⊘ use a number (0-21600) or a preset: `off`, `slow`, `medium`, `fast`, `very slow`, `extreme`",
                    color=0xff4500
                ))

        if seconds < 0 or seconds > 21600:
            return await ctx.send(embed=discord.Embed(
                title="⊘ invalid value",
                description="must be between `0` and `21600` (6 hours).",
                color=0xff4500
            ))

        await ctx.channel.edit(slowmode_delay=seconds)

        if seconds == 0:
            desc = f"◈ slowmode disabled in {ctx.channel.mention}."
        else:
            h, r = divmod(seconds, 3600)
            m, s = divmod(r, 60)
            parts = []
            if h: parts.append(f"{h}h")
            if m: parts.append(f"{m}m")
            parts.append(f"{s}s")
            human = " ".join(parts)
            desc = f"◈ slowmode set to **{human}** in {ctx.channel.mention}."

        await ctx.send(embed=discord.Embed(description=desc, color=0x2b2d31))

async def setup(bot) -> None:
    await bot.add_cog(Slowmode(bot))