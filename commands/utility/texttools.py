import discord
import pyfiglet
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType

class TextTools(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="mock", description="mOcK tExT lIkE tHiS", help="Alternate letter casing to mock text.")
    @cooldown(1, 3, BucketType.user)
    async def mock(self, ctx, *, text: str):
        result = "".join(c.upper() if i % 2 else c.lower() for i, c in enumerate(text))
        embed = discord.Embed(description=result[:2000], color=0x2b2d31)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="reverse", aliases=["rev"], description="reverse a string", help="Reverse the order of characters in text.")
    async def reverse(self, ctx, *, text: str):
        result = text[::-1]
        embed = discord.Embed(description=result[:2000], color=0x2b2d31)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="uppercase", aliases=["upper", "caps"], description="convert text to uppercase", help="Convert text to all uppercase letters.")
    async def uppercase(self, ctx, *, text: str):
        embed = discord.Embed(description=text.upper()[:2000], color=0x2b2d31)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="lowercase", aliases=["lower"], description="convert text to lowercase", help="Convert text to all lowercase letters.")
    async def lowercase(self, ctx, *, text: str):
        embed = discord.Embed(description=text.lower()[:2000], color=0x2b2d31)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="clap", description="add 👏 between 👏 each 👏 word", help="Add clap emoji between each word for emphasis.")
    async def clap(self, ctx, *, text: str):
        result = " 👏 ".join(text.split())
        embed = discord.Embed(description=result[:2000], color=0x2b2d31)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="uwu", description="uwuify your text", help="Transform text with uwu speech patterns. Replaces r/l with w, adds uwu at the end.")
    async def uwu(self, ctx, *, text: str):
        result = text.replace("r", "w").replace("l", "w").replace("R", "W").replace("L", "W")
        result = result.replace("no", "nyo").replace("No", "Nyo").replace("na", "nya").replace("Na", "Nya")
        result += " uwu"
        embed = discord.Embed(description=result[:2000], color=0xff69b4)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="ascii", description="convert text to ascii art", help="Convert text to ASCII art. Choose a font or use default. Fonts: standard, big, block, bubble, digital, slant, small, script. Usage: !ascii hello, !ascii big hello")
    @cooldown(1, 5, BucketType.user)
    async def ascii(self, ctx, font: str = "standard", *, text: str = None):
        if text is None:
            text = font
            font = "standard"

        available_fonts = ["standard", "big", "block", "bubble", "digital", "slant", "small", "script"]
        if font not in available_fonts:
            return await ctx.send(embed=discord.Embed(
                description=f"⊘ font must be one of: `{'`, `'.join(available_fonts)}`",
                color=0xff4500
            ))

        if len(text) > 20:
            return await ctx.send(embed=discord.Embed(
                description="⊘ max 20 characters for ascii art.",
                color=0xff4500
            ))

        result = pyfiglet.figlet_format(text, font=font)
        if len(result) > 1900:
            result = result[:1900]
        await ctx.send(f"```\n{result}\n```")

async def setup(bot) -> None:
    await bot.add_cog(TextTools(bot))