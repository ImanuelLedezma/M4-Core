import discord
import random
import string
import time
from discord.ext import commands, tasks
from helpers.config import get_config
from commands.economy.codes import load_codes, save_codes

DROP_CHANNEL_ID = get_config("codedrop.channel_id", 1491254006117564496)
DROP_INTERVAL = 5
DROP_CHANCE = 0.25
CODE_EXPIRE_SECONDS = 600

DROPPER_PERSONAS = [
    "a mysterious figure", "a stray bot", "the system", "a generous anon",
    "a loot goblin", "a passing fairy", "a glitch in the matrix",
    "a rogue ai", "a time traveler", "your future self",
]

def generate_code(length=5):
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))

class CodeDrop(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.drop_loop.start()
        self.cleanup_loop.start()

    def cog_unload(self) -> None:
        self.drop_loop.cancel()
        self.cleanup_loop.cancel()

    @tasks.loop(minutes=DROP_INTERVAL)
    async def drop_loop(self):
        if random.random() > DROP_CHANCE:
            return

        channel = self.bot.get_channel(DROP_CHANNEL_ID)
        if not channel:
            return

        codes = load_codes()
        code = generate_code().upper()
        while code in codes:
            code = generate_code().upper()

        amount = random.randint(250, 500)
        uses = random.randint(1, 5)
        expiry = time.time() + CODE_EXPIRE_SECONDS
        persona = random.choice(DROPPER_PERSONAS)

        embed = discord.Embed(title="╼ code drop ╾", color=0xfee75c)
        embed.description = (
            f"*{persona} dropped a code...*\n\n"
            f"code: `{code}`\n"
            f"amount: ⌬ {amount:,}\n"
            f"uses: {uses}\n\n"
            f"use `!redeem {code}` to claim!\n"
            f"expires <t:{int(expiry)}:R>."
        )

        msg = await channel.send(embed=embed)

        codes[code] = {
            "amount": amount,
            "uses": uses,
            "redeemed_by": [],
            "expires_at": expiry,
            "message_id": msg.id,
        }
        save_codes(codes)

    @tasks.loop(seconds=30)
    async def cleanup_loop(self):
        codes = load_codes()
        if not codes:
            return

        changed = False
        now = time.time()
        channel = self.bot.get_channel(DROP_CHANNEL_ID)

        for code_str, data in list(codes.items()):
            expires = data.get("expires_at")
            if expires is not None and now > expires:
                if channel and data.get("message_id"):
                    try:
                        msg = channel.get_partial_message(data["message_id"])
                        expired_embed = discord.Embed(title="╼ code drop! ╾", color=0x555555)
                        expired_embed.description = "⊘ this drop has expired"
                        await msg.edit(embed=expired_embed)
                    except (discord.Forbidden, discord.NotFound):
                        pass

                del codes[code_str]
                changed = True

        if changed:
            save_codes(codes)

    @drop_loop.before_loop
    async def before_drop_loop(self):
        await self.bot.wait_until_ready()

    @cleanup_loop.before_loop
    async def before_cleanup_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot) -> None:
    await bot.add_cog(CodeDrop(bot))