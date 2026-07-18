import discord
from discord.ext import commands
from helpers.admins_config import load_admins, save_admins, is_admin

class Admins(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="admin", description="add a user to the admin list", help="Add a user to the bot admin list, granting access to maintenance commands. Admin only.")
    async def add_admin(self, ctx, member: discord.Member):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized", color=0xff4500))

        admins = load_admins()
        if member.id in admins:
            return await ctx.send(embed=discord.Embed(
                description=f"⊘ {member.display_name.lower()} is already an admin!",
                color=0xff4500
            ))

        admins.add(member.id)
        save_admins(admins)
        await ctx.send(embed=discord.Embed(
            description=f"√ {member.display_name.lower()} added to admins",
            color=0x57f287
        ))

    @commands.hybrid_command(name="rmadmin", description="remove a user from the admin list", help="Remove a user from the bot admin list. You can't remove yourself. Admin only.")
    async def remove_admin(self, ctx, member: discord.Member):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized", color=0xff4500))

        admins = load_admins()
        if member.id not in admins:
            return await ctx.send(embed=discord.Embed(
                description=f"⊘ {member.display_name.lower()} is not an admin!",
                color=0xff4500
            ))

        if member.id == ctx.author.id:
            return await ctx.send(embed=discord.Embed(
                description="⊘ you can't remove yourself!",
                color=0xff4500
            ))

        admins.discard(member.id)
        save_admins(admins)
        await ctx.send(embed=discord.Embed(
            description=f"√ {member.display_name.lower()} removed from admins",
            color=0x57f287
        ))

    @commands.hybrid_command(name="adminlist", description="list all bot admins", help="Shows all users with bot admin access.")
    async def admin_list(self, ctx):
        admins = load_admins()
        if not admins:
            return await ctx.send(embed=discord.Embed(description="⊘ no admins configured!", color=0xff4500))

        lines = []
        for uid in sorted(admins):
            member = ctx.guild.get_member(uid)
            lines.append(f"◈ {member.display_name.lower()} (`{uid}`)" if member else f"◈ `{uid}` *(not in server)*")

        await ctx.send(embed=discord.Embed(
            title="╼ admins ╾",
            description="\n".join(lines),
            color=0x2b2d31
        ))

async def setup(bot) -> None:
    await bot.add_cog(Admins(bot))
