import discord
from discord.ext import commands
from helpers.database import rr_get, rr_set, rr_delete, rr_all

class ReactionRoles(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="reactionrole", aliases=["rr", "addrr"], description="add a reaction role to a message", help="Add a reaction role to a message. Usage: !rr #channel message_id :emoji: @role. Reacting with the emoji gives the role, unreacting removes it. Requires Manage Roles permission.")
    @commands.has_permissions(manage_roles=True)
    async def add_rr(self, ctx, channel: discord.TextChannel, message_id: str, emoji: str, role: discord.Role):
        if role >= ctx.guild.me.top_role:
            return await ctx.send(embed=discord.Embed(
                description="⊘ that role is higher than my top role.", color=0xff4500
            ))
        if role == ctx.guild.default_role:
            return await ctx.send(embed=discord.Embed(
                description="⊘ can't use @everyone.", color=0xff4500
            ))

        try:
            mid = int(message_id)
            msg = await channel.fetch_message(mid)
        except (ValueError, discord.NotFound):
            return await ctx.send(embed=discord.Embed(
                description="✖ message not found. make sure the id is correct and i can see the channel.",
                color=0xff4500
            ))
        except discord.Forbidden:
            return await ctx.send(embed=discord.Embed(
                description="⊘ i can't access that channel.", color=0xff4500
            ))

        try:
            await msg.add_reaction(emoji)
        except (discord.Forbidden, discord.NotFound, discord.InvalidArgument):
            return await ctx.send(embed=discord.Embed(
                description=f"✖ invalid emoji `{emoji}` or i can't react there.",
                color=0xff4500
            ))

        key = f"{channel.id}:{mid}:{emoji}"
        rr_set(key, role.id)

        await ctx.send(embed=discord.Embed(
            description=f"√ reaction role set: {emoji} → {role.mention} in {channel.mention}",
            color=0x57f287
        ))

    @commands.hybrid_command(name="removerr", aliases=["delrr", "deleterr"], description="remove a reaction role", help="Remove a reaction role binding. Usage: !removerr #channel message_id :emoji:. Requires Manage Roles permission.")
    @commands.has_permissions(manage_roles=True)
    async def remove_rr(self, ctx, channel: discord.TextChannel, message_id: str, emoji: str):
        key = f"{channel.id}:{message_id}:{emoji}"
        if rr_get(key) is None:
            return await ctx.send(embed=discord.Embed(
                description=f"⊘ no reaction role found for `{emoji}` on that message.",
                color=0xff4500
            ))
        rr_delete(key)
        await ctx.send(embed=discord.Embed(
            description=f"√ reaction role removed for {emoji}",
            color=0x57f287
        ))

    @commands.hybrid_command(name="listrr", aliases=["rrlist"], description="list all reaction roles in this server", help="Shows all configured reaction roles in the server with emoji, channel, and role.")
    async def list_rr(self, ctx):
        data = rr_all()
        channel_keys = [k for k in data if k.split(":")[0].isdigit() and ctx.guild.get_channel(int(k.split(":")[0]))]
        if not channel_keys:
            return await ctx.send(embed=discord.Embed(
                description="no reaction roles set up in this server.", color=0x2b2d31
            ))

        lines = []
        for key in channel_keys:
            cid, mid, emoji = key.split(":", 2)
            ch = ctx.guild.get_channel(int(cid))
            role = ctx.guild.get_role(data[key])
            ch_name = ch.mention if ch else "deleted-channel"
            role_name = role.mention if role else "deleted-role"
            lines.append(f"{emoji} in {ch_name} → {role_name} (`{mid[:8]}...`)")

        await ctx.send(embed=discord.Embed(
            title=f"reaction roles ({len(lines)})",
            description="\n".join(lines),
            color=0x2b2d31
        ))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return
        role_id = rr_get(f"{payload.channel_id}:{payload.message_id}:{payload.emoji.name}")
        if role_id is None and payload.emoji.id:
            for fmt in (f"<:{payload.emoji.name}:{payload.emoji.id}>", f"<a:{payload.emoji.name}:{payload.emoji.id}>"):
                role_id = rr_get(f"{payload.channel_id}:{payload.message_id}:{fmt}")
                if role_id is not None:
                    break
        if role_id is None:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        role = guild.get_role(role_id)
        if not role:
            return
        member = guild.get_member(payload.user_id)
        if not member:
            return

        try:
            await member.add_roles(role, reason="reaction role")
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return
        role_id = rr_get(f"{payload.channel_id}:{payload.message_id}:{payload.emoji.name}")
        if role_id is None and payload.emoji.id:
            for fmt in (f"<:{payload.emoji.name}:{payload.emoji.id}>", f"<a:{payload.emoji.name}:{payload.emoji.id}>"):
                role_id = rr_get(f"{payload.channel_id}:{payload.message_id}:{fmt}")
                if role_id is not None:
                    break
        if role_id is None:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        role = guild.get_role(role_id)
        if not role:
            return
        member = guild.get_member(payload.user_id)
        if not member:
            return

        try:
            await member.remove_roles(role, reason="reaction role removed")
        except (discord.Forbidden, discord.HTTPException):
            pass

async def setup(bot) -> None:
    await bot.add_cog(ReactionRoles(bot))
