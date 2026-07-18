import asyncio
import discord
from discord.ext import commands

class Ban(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def _confirm(self, ctx, target: discord.Member, action: str) -> bool:
        embed = discord.Embed(
            title=f"⚠ confirm {action}",
            description=f"are you sure you want to {action} {target.mention}?",
            color=0xf1c40f
        )
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        def check(r, u):
            return u == ctx.author and r.message.id == msg.id and str(r.emoji) in ("✅", "❌")
        try:
            r, _ = await self.bot.wait_for("reaction_add", timeout=15.0, check=check)
        except asyncio.TimeoutError:
            await msg.edit(embed=discord.Embed(description="⊘ timed out.", color=0xff4500))
            return False
        try:
            await msg.clear_reactions()
        except (discord.Forbidden, discord.NotFound):
            pass
        return str(r.emoji) == "✅"

    @commands.hybrid_command(name="ban", description="ban a member from the server", help="Ban a member from the server. Requires Ban Members permission. DMs the user with reason. Requires confirmation via ✅. Can't ban users with equal or higher role.")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = "no reason provided"):
        if member == ctx.author:
            return await ctx.send(embed=discord.Embed(
                title="⊘ invalid target", description="you can't ban yourself.", color=0xff4500
            ))
        if member.top_role >= ctx.author.top_role:
            return await ctx.send(embed=discord.Embed(
                title="⊘ insufficient hierarchy",
                description="you can't ban someone with an equal or higher role.",
                color=0xff4500
            ))
        if not await self._confirm(ctx, member, "ban"):
            return

        try:
            await member.send(embed=discord.Embed(
                title=f"you've been banned from {ctx.guild.name}",
                description=f"**reason:** {reason}\n**by:** {ctx.author.name}",
                color=0xff4500
            ))
        except discord.Forbidden:
            pass

        await member.ban(reason=reason)
        await ctx.send(embed=discord.Embed(
            title="√ banned",
            description=f"banned {member.mention} · **{reason}**",
            color=0x57f287
        ))

    @commands.hybrid_command(name="unban", description="unban a user by id or name", help="Unban a user by their ID number or by searching their username. Requires Ban Members permission.")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, identifier: str):
        try:
            user_id = int(identifier)
            user = await self.bot.fetch_user(user_id)
        except ValueError:
            bans = [entry async for entry in ctx.guild.bans()]
            match = None
            for ban_entry in bans:
                if identifier.lower() in ban_entry.user.name.lower():
                    match = ban_entry.user
                    break
            if not match:
                return await ctx.send(embed=discord.Embed(
                    title="⊘ not found",
                    description=f"no banned user matching `{identifier}`.",
                    color=0xff4500
                ))
            user = match

        await ctx.guild.unban(user, reason=f"unbanned by {ctx.author}")
        await ctx.send(embed=discord.Embed(
            title="√ unbanned",
            description=f"unbanned `{user.name}`",
            color=0x57f287
        ))

    @commands.hybrid_command(name="bans", description="list banned users", help="Shows all banned users with their user ID and ban reason. Requires Ban Members permission.")
    @commands.has_permissions(ban_members=True)
    async def list_bans(self, ctx):
        bans = [entry async for entry in ctx.guild.bans()]
        if not bans:
            return await ctx.send(embed=discord.Embed(
                description="no banned users.",
                color=0x2b2d31
            ))
        chunks = [bans[i:i + 30] for i in range(0, len(bans), 30)]
        for chunk in chunks:
            embed = discord.Embed(title=f"bans ({len(bans)} total)", color=0x2b2d31)
            for entry in chunk:
                embed.add_field(
                    name=str(entry.user),
                    value=f"id: `{entry.user.id}` · reason: {entry.reason or 'none'}",
                    inline=False
                )
            await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Ban(bot))