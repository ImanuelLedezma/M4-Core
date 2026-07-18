import discord
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType

class Avatar(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="avatar", aliases=["av", "pfp"], description="show a user's profile picture", help="Show a user's profile picture. Optionally specify format: !av @user png, !av @user gif, !av @user jpeg. Defaults to PNG at 4096px.")
    @cooldown(1, 3, BucketType.user)
    async def avatar(self, ctx, member: discord.Member = None, fmt: str = None):
        member = member or ctx.author
        fmt = (fmt or "png").lower().replace("jpg", "jpeg")

        avatar = member.display_avatar

        if fmt == "gif":
            fmt = "gif"
        elif fmt not in ("png", "jpeg", "webp"):
            fmt = "png"

        url = avatar.replace(format=fmt, size=4096).url if fmt != "gif" else avatar.url

        embed = discord.Embed(
            title=f"{member.name}'s avatar",
            color=member.color if member.color.value else 0x5865f2
        )
        embed.set_image(url=url)
        embed.set_footer(text=f"{fmt.upper()} · {url.split('?')[0].rsplit('/', 1)[-1]}")
        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Avatar(bot))