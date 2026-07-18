import asyncio
import discord
from discord.ext import commands
from helpers.time_utils import parse_duration

class Timeout(commands.Cog):
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

    @commands.hybrid_command(name="timeout", aliases=["mute"], description="timeout a member for a duration", help="Timeout a member for a duration. Formats: 10s, 5m, 2h, 1d. Max 28 days. Requires Moderate Members permission. Requires confirmation via ✅.")
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, duration: str, *, reason: str = "no reason provided"):
        if member == ctx.author:
            return await ctx.send(embed=discord.Embed(
                title="⊘ invalid target", description="you can't timeout yourself.", color=0xff4500
            ))
        if member.top_role >= ctx.author.top_role:
            return await ctx.send(embed=discord.Embed(
                title="⊘ insufficient hierarchy", description="you can't timeout someone with an equal or higher role.", color=0xff4500
            ))

        delta = parse_duration(duration)
        if not delta:
            return await ctx.send(embed=discord.Embed(
                title="⊘ invalid duration",
                description="use format: `10s`, `5m`, `2h`, `1d`",
                color=0xff4500
            ))
        if delta.total_seconds() > 60 * 60 * 24 * 28:
            return await ctx.send(embed=discord.Embed(
                title="⊘ too long", description="max timeout is 28 days.", color=0xff4500
            ))
        if not await self._confirm(ctx, member, f"timeout for {duration}"):
            return

        await member.timeout(delta, reason=reason)

        try:
            await member.send(embed=discord.Embed(
                title=f"you've been timed out in {ctx.guild.name}",
                description=f"**duration:** {duration}\n**reason:** {reason}\n**by:** {ctx.author.name}",
                color=0xff4500
            ))
        except discord.Forbidden:
            pass

        await ctx.send(embed=discord.Embed(
            title="√ timed out",
            description=f"timed out {member.mention} for **{duration}** · {reason}",
            color=0x57f287
        ))

    @commands.hybrid_command(name="untimeout", aliases=["unmute"], description="remove a timeout from a member", help="Remove an active timeout from a member. Requires Moderate Members permission.")
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx, member: discord.Member):
        if not member.is_timed_out():
            return await ctx.send(embed=discord.Embed(
                description="⊘ that member is not timed out.", color=0xff4500
            ))
        await member.timeout(None)
        await ctx.send(embed=discord.Embed(
            description=f"√ removed timeout from {member.mention}.", color=0x57f287
        ))

async def setup(bot) -> None:
    await bot.add_cog(Timeout(bot))
