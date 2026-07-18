import discord
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType
import qrcode
import io

class QR(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="qr", description="generate or read qr codes", help="Generate a QR code from text/URL, or decode one from an attached image. Usage: !qr https://example.com, !qr read (with attached image)")
    @cooldown(1, 5, BucketType.user)
    async def qr(self, ctx, *, text_or_action: str = None):
        if text_or_action and text_or_action.lower().startswith("read"):
            return await self._read_qr(ctx)

        text = text_or_action
        if not text:
            if ctx.message.attachments:
                return await self._read_qr(ctx)
            return await ctx.send(embed=discord.Embed(
                description="✖ usage: `!qr <text>`, `!qr read` with an image, or attach an image to decode",
                color=0xff4500
            ))

        img = qrcode.make(text)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        await ctx.send(
            embed=discord.Embed(description=f"◈ qr for: `{text[:80]}`", color=0x2b2d31),
            file=discord.File(buf, filename="qr.png")
        )

    async def _read_qr(self, ctx):
        if not ctx.message.attachments:
            return await ctx.send(embed=discord.Embed(
                description="✖ attach an image containing a qr code.",
                color=0xff4500
            ))

        attachment = ctx.message.attachments[0]
        if not attachment.content_type or not attachment.content_type.startswith("image"):
            return await ctx.send(embed=discord.Embed(
                description="✖ the attachment must be an image.",
                color=0xff4500
            ))

        try:
            from pyzbar.pyzbar import decode
            from PIL import Image as PILImage
        except ImportError:
            return await ctx.send(embed=discord.Embed(
                description="✖ qr reading requires `pyzbar` and `pyzbar[windows]` (not installed).",
                color=0xff4500
            ))

        img_bytes = await attachment.read()
        try:
            img = PILImage.open(io.BytesIO(img_bytes))
        except Exception:
            return await ctx.send(embed=discord.Embed(
                description="✖ could not decode the image.",
                color=0xff4500
            ))

        decoded = decode(img)
        if not decoded:
            return await ctx.send(embed=discord.Embed(
                description="✖ no qr code detected in the image.",
                color=0xff4500
            ))

        results = []
        for obj in decoded:
            results.append(f"`{obj.data.decode('utf-8')[:200]}`")

        await ctx.send(embed=discord.Embed(
            title="◈ qr decoded",
            description="\n".join(results),
            color=0x2b2d31
        ))

async def setup(bot) -> None:
    await bot.add_cog(QR(bot))