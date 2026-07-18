import discord
from discord.ext import commands

class Nick(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="nick", aliases=["nickname"], description="change a member's nickname", help="Change or remove a member's server nickname. Use !nick <user> <name> to set, !nick <user> clear to reset. Requires Manage Nicknames permission.")
    @commands.has_permissions(manage_nicknames=True)
    async def nick(self, ctx, member: discord.Member, *, nickname: str = None):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send(embed=discord.Embed(
                description="⊘ you can't change the nickname of someone with an equal or higher role.",
                color=0xff4500
            ))

        if nickname and nickname.lower() in ("clear", "reset", "remove"):
            nickname = None

        try:
            await member.edit(nick=nickname, reason=f"changed by {ctx.author}")
        except discord.Forbidden:
            return await ctx.send(embed=discord.Embed(
                description="⊘ i don't have permission to change that member's nickname.",
                color=0xff4500
            ))

        if nickname:
            await ctx.send(embed=discord.Embed(
                description=f"√ set {member.mention}'s nickname to **{nickname}**",
                color=0x57f287
            ))
        else:
            await ctx.send(embed=discord.Embed(
                description=f"√ reset {member.mention}'s nickname",
                color=0x57f287
            ))

async def setup(bot) -> None:
    await bot.add_cog(Nick(bot))
