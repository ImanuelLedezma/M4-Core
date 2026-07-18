import time
from discord.ext import commands, tasks
from helpers.config import get_config
from helpers.economy_base import load_bank, save_bank
from helpers.database import departed_set, departed_get, departed_remove, departed_all, departed_expire

PURGE_AFTER = get_config("prune.purge_after_days", 15) * 86400

class Prune(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.purge_loop.start()

    def cog_unload(self) -> None:
        self.purge_loop.cancel()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        departed_set(member.id, time.time())

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if departed_get(member.id) is not None:
            departed_remove(member.id)

    @tasks.loop(hours=24)
    async def purge_loop(self):
        if not departed_all():
            return

        bank = load_bank()
        cutoff = time.time() - PURGE_AFTER
        expired = departed_expire(cutoff)
        if not expired:
            return

        changed = False
        for uid in expired:
            uid_str = str(uid)
            if uid_str in bank:
                del bank[uid_str]
                changed = True

        if changed:
            save_bank(bank)

    @purge_loop.before_loop
    async def before_purge_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot) -> None:
    await bot.add_cog(Prune(bot))
