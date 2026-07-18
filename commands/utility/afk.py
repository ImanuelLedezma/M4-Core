import asyncio
import discord
from discord.ext import commands
from helpers.storage import load, save

AFK_FILE = "afk.msgpack"

class Afk(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def _load_all(self) -> dict:
        return await asyncio.to_thread(load, AFK_FILE)

    async def _save_all(self, data: dict) -> None:
        await asyncio.to_thread(save, AFK_FILE, data)

    @commands.hybrid_command(name="afk", description="set your status as away", help="Set your status as away. When someone mentions you, the bot will tell them you're AFK with your reason. Your AFK is automatically removed when you send a message. Persists across bot restarts.")
    async def afk(self, ctx, *, reason: str = "afk"):
        data = await self._load_all()
        data[str(ctx.author.id)] = {
            "reason": reason,
            "at": discord.utils.utcnow().isoformat(),
        }
        await self._save_all(data)
        await ctx.send(embed=discord.Embed(
            title="√ afk set",
            description=f"{ctx.author.mention} is now afk · **{reason}**",
            color=discord.Color.blue()
        ))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        data = await self._load_all()
        uid = str(message.author.id)

        if uid in data:
            del data[uid]
            await self._save_all(data)
            await message.channel.send(embed=discord.Embed(
                title="√ welcome back",
                description=f"{message.author.mention} your afk has been removed.",
                color=discord.Color.green()
            ))

        if message.mentions:
            for member in message.mentions:
                mid = str(member.id)
                if mid in data:
                    entry = data[mid]
                    try:
                        at = discord.utils.parse_time(entry["at"])
                        delta = discord.utils.utcnow() - at
                        mins = int(delta.total_seconds() // 60)
                        time_str = f"`{mins}m ago`" if mins > 0 else "`just now`"
                    except Exception:
                        time_str = "`unknown`"
                    await message.channel.send(embed=discord.Embed(
                        title="⌖ user is afk",
                        description=f"{member.mention} is afk · **{entry['reason']}** · {time_str}",
                        color=discord.Color.yellow()
                    ))

async def setup(bot) -> None:
    await bot.add_cog(Afk(bot))