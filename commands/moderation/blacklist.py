import discord
from discord.ext import commands
from helpers.admins_config import is_admin
from helpers.blacklist_config import load_blacklist, save_blacklist

class Blacklist(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="blacklist", description="block a user from using commands", help="Add a user to the blacklist, preventing them from using any bot commands. Admin only.")
    async def add_blacklist(self, ctx, member: discord.Member):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized", color=0xff4500))
        if member.id == ctx.author.id:
            return await ctx.send(embed=discord.Embed(description="⊘ you can't blacklist yourself!", color=0xff4500))

        bl = load_blacklist()
        if member.id in bl:
            return await ctx.send(embed=discord.Embed(
                description=f"⊘ {member.display_name.lower()} is already blacklisted!",
                color=0xff4500
            ))

        bl.add(member.id)
        save_blacklist(bl)
        await ctx.send(embed=discord.Embed(
            description=f"√ blacklisted {member.mention} (`{member.id}`)",
            color=0x57f287
        ))

    @commands.hybrid_command(name="unblacklist", aliases=["rmblacklist"], description="unblock a user", help="Remove a user from the blacklist. Admin only.")
    async def remove_blacklist(self, ctx, member: discord.Member):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized", color=0xff4500))

        bl = load_blacklist()
        if member.id not in bl:
            return await ctx.send(embed=discord.Embed(
                description=f"⊘ {member.display_name.lower()} is not blacklisted!",
                color=0xff4500
            ))

        bl.discard(member.id)
        save_blacklist(bl)
        await ctx.send(embed=discord.Embed(
            description=f"√ {member.mention} removed from blacklist",
            color=0x57f287
        ))

    @commands.hybrid_command(name="blacklistlist", aliases=["bllist", "blacklisted"], description="list all blacklisted users", help="Shows all blacklisted users with their user IDs. Admin only.")
    async def list_blacklist(self, ctx):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized", color=0xff4500))

        bl = load_blacklist()
        if not bl:
            return await ctx.send(embed=discord.Embed(description="no users are blacklisted.", color=0x2b2d31))

        lines = []
        for uid in sorted(bl):
            user = self.bot.get_user(uid)
            name = user.display_name if user else f"unknown ({uid})"
            lines.append(f"`{uid}` · {name}")

        await ctx.send(embed=discord.Embed(
            title=f"blacklist ({len(bl)})",
            description="\n".join(lines),
            color=0x2b2d31
        ))

async def setup(bot) -> None:
    await bot.add_cog(Blacklist(bot))