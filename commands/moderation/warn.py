import discord
from discord.ext import commands
from helpers.database import warn_add, warn_count, warn_list, warn_remove
from helpers.config import get_channel_id

LOG_CHANNEL_ID = get_channel_id("log")

class Warn(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def _log(self, guild, embed):
        if not guild:
            return
        ch = guild.get_channel(LOG_CHANNEL_ID)
        if ch:
            await ch.send(embed=embed)

    @commands.hybrid_command(name="warn", description="warn a user", help="Warn a user with a reason. Tracks total warnings per user. Use !warnings to view. Requires Moderate Members permission.")
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = "no reason"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send(embed=discord.Embed(
                description="⊘ you can't warn someone with an equal or higher role.", color=0xff4500
            ))

        warn_add(ctx.guild.id, member.id, reason, ctx.author.id)
        total = warn_count(ctx.guild.id, member.id)

        await ctx.send(embed=discord.Embed(
            title="√ warning issued",
            description=f"{member.mention} has been warned · **{reason}**\nthis is warning **#{total}**",
            color=0xf1c40f
        ))
        await self._log(ctx.guild, discord.Embed(
            title="⚠ warning issued", color=0xf1c40f, timestamp=discord.utils.utcnow()
        ).add_field(name="user", value=member.mention).add_field(name="moderator", value=ctx.author.mention).add_field(name="reason", value=reason, inline=False).add_field(name="total warnings", value=str(total)))

    @commands.hybrid_command(name="warnings", aliases=["warns"], description="view warnings for a user", help="Shows all warnings issued to a user with ID, reason, and moderator. Requires Moderate Members permission.")
    @commands.has_permissions(moderate_members=True)
    async def warnings(self, ctx, member: discord.Member):
        warns = warn_list(ctx.guild.id, member.id)
        if not warns:
            return await ctx.send(embed=discord.Embed(
                description=f"{member.mention} has no warnings.", color=0x2b2d31
            ))

        lines = []
        for w in warns:
            mod = ctx.guild.get_member(w["moderator_id"])
            mod_name = mod.mention if mod else f"`{w['moderator_id']}`"
            lines.append(f"`#{w['id']}` · {w['reason']} · by {mod_name}")
        embed = discord.Embed(title=f"warnings for {member.display_name}", description="\n".join(lines), color=0xf1c40f)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="delwarn", aliases=["removewarn", "unwarn"], description="remove a specific warning by id", help="Remove a warning by its ID number. Use !warnings to find the ID. Requires Moderate Members permission.")
    @commands.has_permissions(moderate_members=True)
    async def delwarn(self, ctx, warn_id: int):
        if warn_remove(warn_id):
            await ctx.send(embed=discord.Embed(description=f"√ removed warning `#{warn_id}`", color=0x57f287))
        else:
            await ctx.send(embed=discord.Embed(description=f"⊘ warning `#{warn_id}` not found.", color=0xff4500))

async def setup(bot) -> None:
    await bot.add_cog(Warn(bot))
