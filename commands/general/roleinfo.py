import discord
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType

PERMISSION_EMOJIS = {
    "administrator": "🛡", "ban_members": "🔨", "kick_members": "👢",
    "manage_channels": "📡", "manage_guild": "⚙", "manage_messages": "✉",
    "manage_roles": "👑", "manage_webhooks": "🪝", "moderate_members": "🔇",
    "mention_everyone": "📢", "send_messages": "💬", "attach_files": "📎",
    "embed_links": "🔗", "add_reactions": "➕",
}

class RoleInfo(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="roleinfo", aliases=["ri", "role"], description="show information about a role", help="Shows detailed role info: ID, member count, color, mentionable/hoisted/managed status, position, creation date, and permissions with emoji icons.")
    @cooldown(1, 3, BucketType.user)
    async def roleinfo(self, ctx, *, role: discord.Role):
        perms = []
        for perm, value in role.permissions:
            if value:
                emoji = PERMISSION_EMOJIS.get(perm, "")
                perms.append(f"{emoji} {perm.replace('_', ' ')}")

        created = role.created_at.strftime("%b %d, %Y")

        embed = discord.Embed(
            title=role.name,
            color=role.color if role.color.value else discord.Color.blue()
        )
        embed.add_field(name="id", value=f"`{role.id}`", inline=True)
        embed.add_field(name="members", value=f"`{len(role.members)}`", inline=True)
        embed.add_field(name="color", value=f"`{str(role.color)}`", inline=True)
        embed.add_field(name="mentionable", value="✅" if role.mentionable else "❌", inline=True)
        embed.add_field(name="hoisted", value="✅" if role.hoist else "❌", inline=True)
        embed.add_field(name="position", value=f"`{role.position}`", inline=True)
        embed.add_field(name="created", value=created, inline=True)
        embed.add_field(name="managed", value="✅" if role.managed else "❌", inline=True)

        if perms:
            perm_str = "\n".join(perms)
            if len(perm_str) > 1024:
                perm_str = perm_str[:1020] + "..."
            embed.add_field(name=f"permissions ({len(perms)})", value=perm_str, inline=False)

        embed.set_footer(text=f"requested by {ctx.author.name}")
        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(RoleInfo(bot))