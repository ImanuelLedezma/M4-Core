import discord
import random
import string
import re
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType

class Generators(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="password", aliases=["pw", "genpass"], description="generate a secure random password", help="Generate a secure random password (8-64 characters). Uses letters, numbers, and special chars. Sent via DM for security.")
    @cooldown(1, 5, BucketType.user)
    async def password(self, ctx, length: int = 16):
        if length < 8:
            return await ctx.send(embed=discord.Embed(
                title="✖ too short", description="minimum length is `8`.", color=discord.Color.red()
            ))
        if length > 64:
            return await ctx.send(embed=discord.Embed(
                title="✖ too long", description="maximum length is `64`.", color=discord.Color.red()
            ))

        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        pw = "".join(random.choices(chars, k=length))

        try:
            await ctx.author.send(embed=discord.Embed(
                title="√ generated password",
                description=f"```\n{pw}\n```",
                color=discord.Color.green()
            ).set_footer(text="sent via dms"))
            await ctx.send(embed=discord.Embed(
                title="√ password sent", description="check your dms", color=discord.Color.green()
            ))
        except discord.Forbidden:
            await ctx.send(embed=discord.Embed(
                title="✖ dms closed",
                description="i can't dm you, open your dms and try again",
                color=discord.Color.red()
            ))

    @commands.command(name="dice", aliases=["roll"], description="roll dice", help="Roll dice. Formats: !roll 6 (single die), !roll 2d6 (two six-sided), !roll 3d20 (three twenty-sided). Max 20 dice, max 1000 sides.")
    @cooldown(1, 3, BucketType.user)
    async def dice(self, ctx, *args):
        formula = " ".join(args) if args else "1d6"
        match = re.fullmatch(r"(\d+)?d(\d+)", formula.lower().replace(" ", ""))
        if match:
            count = int(match.group(1)) if match.group(1) else 1
            sides = int(match.group(2))
            count = min(count, 20)
            sides = min(sides, 1000)
            if count < 1 or sides < 2:
                return await ctx.send(embed=discord.Embed(
                    title="✖ invalid dice", description="use format `2d6` or `d20`.", color=discord.Color.red()
                ))
            results = [random.randint(1, sides) for _ in range(count)]
            total = sum(results)
            desc = f"rolled `{' + '.join(str(r) for r in results)}`"
            if count > 1:
                desc += f"\n**total: {total}**"
            embed = discord.Embed(title=f"⚄ {count}d{sides}", description=desc, color=discord.Color.blue())
            return await ctx.send(embed=embed)

        sides_match = re.fullmatch(r"(\d+)", formula)
        if sides_match:
            sides = int(sides_match.group(1))
            if sides < 2 or sides > 1000:
                return await ctx.send(embed=discord.Embed(
                    title="✖ invalid sides",
                    description="use a number between `2` and `1000`, or `NdN` format.",
                    color=discord.Color.red()
                ))
            result = random.randint(1, sides)
            return await ctx.send(embed=discord.Embed(
                title=f"⚄ d{sides}",
                description=f"rolled **{result}**",
                color=discord.Color.blue()
            ))

        await ctx.send(embed=discord.Embed(
            title="✖ invalid format",
            description="use `!roll 6`, `!roll 2d6`, or `!roll 3d20`",
            color=discord.Color.red()
        ))

async def setup(bot) -> None:
    await bot.add_cog(Generators(bot))