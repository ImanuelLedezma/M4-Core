import discord
import time
from discord.ext import commands

class Ping(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="ping", description="check the bot's latency", help="Shows both WebSocket heartbeat latency and REST API round-trip time. Color-coded: green (<150ms), yellow (<300ms), red (300ms+).")
    async def ping(self, ctx):
        ws = round(self.bot.latency * 1000)

        start = time.monotonic()
        msg = await ctx.send(embed=discord.Embed(
            description="⟳ measuring...", color=0x2b2d31
        ))
        rest = round((time.monotonic() - start) * 1000)

        color = 0x57f287 if ws < 150 else (0xf1c40f if ws < 300 else 0xff4500)

        embed = discord.Embed(title="⟳ pong!", color=color)
        embed.add_field(name="websocket", value=f"`{ws}ms`", inline=True)
        embed.add_field(name="rest api", value=f"`{rest}ms`", inline=True)

        await msg.edit(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Ping(bot))