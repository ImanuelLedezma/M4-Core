import discord
from discord.ext import commands
from helpers.config import get_config

class Lock(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    def _get_revoke_roles(self, guild) -> list[int]:
        configured = get_config("lock.revoke_roles")
        if configured:
            return configured
        return [1490701432456876163, 1483259650983067781]

    @commands.hybrid_command(name="lock", description="lock the current channel", help="Lock the current channel by revoking send messages permission from configured roles. Requires Manage Channels permission.")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        overwrites = ctx.channel.overwrites
        revoke_roles = self._get_revoke_roles(ctx.guild)

        for role_id in revoke_roles:
            role = ctx.guild.get_role(role_id)
            if role:
                ow = overwrites.get(role)
                if ow is None:
                    ow = discord.PermissionOverwrite()
                ow.send_messages = False
                overwrites[role] = ow

        await ctx.channel.edit(overwrites=overwrites)
        await ctx.send(embed=discord.Embed(
            description="√ channel locked.",
            color=0xff4500
        ))

    @commands.hybrid_command(name="unlock", description="unlock the current channel", help="Unlock the current channel by resetting send messages permission to neutral. Requires Manage Channels permission.")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        overwrites = ctx.channel.overwrites
        revoke_roles = self._get_revoke_roles(ctx.guild)

        for role_id in revoke_roles:
            role = ctx.guild.get_role(role_id)
            if role:
                ow = overwrites.get(role)
                if ow is None:
                    ow = discord.PermissionOverwrite()
                ow.send_messages = None
                overwrites[role] = ow

        await ctx.channel.edit(overwrites=overwrites)
        await ctx.send(embed=discord.Embed(
            description="√ channel unlocked.",
            color=0x57f287
        ))

async def setup(bot) -> None:
    await bot.add_cog(Lock(bot))
