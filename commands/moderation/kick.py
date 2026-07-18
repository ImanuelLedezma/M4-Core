import asyncio
import discord
from discord.ext import commands

class Kick(commands.Cog):
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

    @commands.hybrid_command(name="kick", description="kick a member from the server", help="Kick a member from the server. Requires Kick Members permission. DMs the user with reason. Requires confirmation via ✅. Can't kick users with equal or higher role.")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "no reason provided"):
        if member == ctx.author:
            return await ctx.send(embed=discord.Embed(
                title="✖ invalid target", description="you can't kick yourself.", color=discord.Color.red()
            ))
        if member.top_role >= ctx.author.top_role:
            return await ctx.send(embed=discord.Embed(
                title="✖ insufficient hierarchy",
                description="you can't kick someone with an equal or higher role.",
                color=discord.Color.red()
            ))
        if not await self._confirm(ctx, member, "kick"):
            return

        try:
            await member.send(embed=discord.Embed(
                title=f"you've been kicked from {ctx.guild.name}",
                description=f"**reason:** {reason}\n**by:** {ctx.author.name}",
                color=discord.Color.red()
            ))
        except discord.Forbidden:
            pass

        await member.kick(reason=reason)
        await ctx.send(embed=discord.Embed(
            title="√ kicked",
            description=f"kicked {member.mention} · **{reason}**",
            color=discord.Color.green()
        ))
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

async def setup(bot) -> None:
    await bot.add_cog(Kick(bot))