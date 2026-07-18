import discord
import asyncio
from discord.ext import commands
import sys
from helpers.admins_config import is_admin

class Restart(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="restart", description="restart the bot process", help="Restart the bot process. Requires confirmation via ✅ reaction. Admin only.")
    async def restart(self, ctx):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized.", color=0xff4500))

        embed = discord.Embed(
            title="⟳ confirm restart",
            description="are you sure? react with ✅ to confirm",
            color=0xf1c40f
        )
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

        def check(r, u):
            return u == ctx.author and r.message.id == msg.id and str(r.emoji) in ("✅", "❌")

        try:
            r, _ = await self.bot.wait_for("reaction_add", timeout=15.0, check=check)
        except asyncio.TimeoutError:
            return await msg.edit(embed=discord.Embed(description="⊘ cancelled (timeout)", color=0xff4500))

        if str(r.emoji) == "❌":
            return await msg.edit(embed=discord.Embed(description="✖ cancelled.", color=0xff4500))

        await msg.edit(embed=discord.Embed(
            title="⟳ restarting",
            description=f"restarting bot... initiated by {ctx.author}",
            color=discord.Color.blue()
        ))

        await asyncio.create_subprocess_exec(
            sys.executable, "main.py",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await self.bot.close()

async def setup(bot) -> None:
    await bot.add_cog(Restart(bot))