import os
import time
import discord
from discord.ext import commands
from helpers.admins_config import load_admins, save_admins

RATE_LIMIT_SECONDS = 300
MAX_ATTEMPTS = 3
WINDOW_SECONDS = 3600

class Emergency(commands.Cog):
    """Emergency admin access via DM passphrase. Rate limited: 3 attempts per hour."""
    def __init__(self, bot) -> None:
        self.bot = bot
        self.passphrase = os.getenv("EMERGENCY_PASSPHRASE")
        self._attempts: dict[int, list[float]] = {}
        self._rate_limited: dict[int, float] = {}

    def _is_rate_limited(self, user_id: int) -> bool:
        now = time.time()
        if user_id in self._rate_limited:
            if now - self._rate_limited[user_id] < RATE_LIMIT_SECONDS:
                return True
            del self._rate_limited[user_id]
        if user_id not in self._attempts:
            self._attempts[user_id] = []
        self._attempts[user_id] = [t for t in self._attempts[user_id] if now - t < WINDOW_SECONDS]
        if len(self._attempts[user_id]) >= MAX_ATTEMPTS:
            self._rate_limited[user_id] = now
            self._attempts[user_id] = []
            return True
        self._attempts[user_id].append(now)
        return False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not isinstance(message.channel, discord.DMChannel):
            return
        if not self.passphrase:
            return

        if self._is_rate_limited(message.author.id):
            return

        if message.content.strip() == self.passphrase:
            admins = load_admins()

            if message.author.id in admins:
                return await message.channel.send(embed=discord.Embed(
                    description="⊘ you already have admin powers",
                    color=0xff4500
                ))

            admins.add(message.author.id)
            save_admins(admins)

            await message.channel.send(embed=discord.Embed(
                description="√ emergency admin access granted",
                color=0x57f287
            ))

async def setup(bot) -> None:
    await bot.add_cog(Emergency(bot))