import time
from discord.ext import commands, tasks
from helpers.config import get_config
from helpers.economy_base import load_bank, save_bank
from helpers.storage import load, save

DEPARTED_FILE = "departed.msgpack"
PURGE_AFTER = get_config("prune.purge_after_days", 15) * 86400

def load_departed():
    return load(DEPARTED_FILE)

def save_departed(data):
    save(DEPARTED_FILE, data)

class AutoPurge(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.purge_loop.start()

    def cog_unload(self) -> None:
        self.purge_loop.cancel()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        departed = load_departed()
        departed[str(member.id)] = time.time()
        save_departed(departed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        departed = load_departed()
        uid = str(member.id)
        if uid in departed:
            del departed[uid]
            save_departed(departed)

    @tasks.loop(hours=24)
    async def purge_loop(self):
        departed = load_departed()
        if not departed:
            return

        bank = load_bank()

        now = time.time()
        changed_departed = False
        changed_bank = False

        for uid, left_at in list(departed.items()):
            if now - left_at >= PURGE_AFTER:
                if uid in bank:
                    del bank[uid]
                    changed_bank = True
                del departed[uid]
                changed_departed = True

        if changed_bank:
            save_bank(bank)

        if changed_departed:
            save_departed(departed)

    @purge_loop.before_loop
    async def before_purge_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot) -> None:
    await bot.add_cog(AutoPurge(bot))