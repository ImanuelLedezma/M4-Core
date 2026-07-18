import discord
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType
import base64 as b64
import binascii

FORMATS = {
    "base64": (b64.b64encode, b64.b64decode),
    "base32": (b64.b32encode, b64.b32decode),
    "base16": (b64.b16encode, b64.b16decode),
    "hex": (lambda x: x.hex().encode(), lambda x: bytes.fromhex(x.decode() if isinstance(x, bytes) else x)),
}

class Base64(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="b64", aliases=["base64", "encode", "decode"], description="encode or decode base64/base32/hex", help="Encode or decode text using base64, base32, or hex. Examples: !b64 encode hello, !b64 decode base32 didgm====, !b64 decode hex 48656c6c6f")
    @cooldown(1, 3, BucketType.user)
    async def b64_cmd(self, ctx, action: str, encoding: str = None, *, text: str = None):
        if encoding and encoding.lower() in FORMATS and text:
            fmt = encoding.lower()
            action = action.lower()
        elif action.lower() in FORMATS:
            fmt = action.lower()
            action = "decode"
            encoding = None
        else:
            action = action.lower()
            fmt = "base64"

        if action not in ("encode", "decode"):
            return await ctx.send(embed=discord.Embed(
                description="✖ usage: `!b64 encode <text>`, `!b64 decode base32 <text>`, `!b64 decode hex <text>`",
                color=0xff4500
            ))

        if not text:
            if encoding:
                text = encoding
            else:
                return await ctx.send(embed=discord.Embed(
                    description="✖ missing text to process.",
                    color=0xff4500
                ))

        enc_func, dec_func = FORMATS[fmt]

        try:
            if action == "encode":
                result = enc_func(text.encode()).decode()
                label = f"◈ encoded ({fmt})"
            else:
                raw = text.encode() if isinstance(text, str) else text
                result = dec_func(raw).decode()
                label = f"◈ decoded ({fmt})"
        except (binascii.Error, ValueError, Exception):
            return await ctx.send(embed=discord.Embed(
                description=f"✖ invalid input for {fmt} decoding.",
                color=0xff4500
            ))

        if len(result) > 1900:
            result = result[:1900] + "..."

        embed = discord.Embed(color=0x2b2d31)
        embed.add_field(name="◈ input", value=f"`{text[:200]}`", inline=False)
        embed.add_field(name=label, value=f"`{result}`", inline=False)
        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Base64(bot))