import discord
from discord.ext import commands

class Move(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="move", description="move a member to another voice channel", help="Move a member from their current voice channel to another. Usage: !move <user> <channel>. Requires Move Members permission.")
    @commands.has_permissions(move_members=True)
    async def move(self, ctx, member: discord.Member, channel: discord.VoiceChannel):
        if not member.voice or not member.voice.channel:
            return await ctx.send(embed=discord.Embed(
                description="⊘ that member is not in a voice channel.",
                color=0xff4500
            ))

        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send(embed=discord.Embed(
                description="⊘ you can't move someone with an equal or higher role.",
                color=0xff4500
            ))

        try:
            await member.move_to(channel, reason=f"moved by {ctx.author}")
        except discord.Forbidden:
            return await ctx.send(embed=discord.Embed(
                description="⊘ i don't have permission to move that member.",
                color=0xff4500
            ))

        await ctx.send(embed=discord.Embed(
            description=f"√ moved {member.mention} to {channel.mention}",
            color=0x57f287
        ))

    @commands.hybrid_command(name="moveall", description="move all members from one voice channel to another", help="Move all members in one voice channel to another. Usage: !moveall <from_channel> <to_channel>. Requires Move Members permission.")
    @commands.has_permissions(move_members=True)
    async def moveall(self, ctx, from_channel: discord.VoiceChannel, to_channel: discord.VoiceChannel):
        members = from_channel.members
        if not members:
            return await ctx.send(embed=discord.Embed(
                description="⊘ no members in that voice channel.",
                color=0xff4500
            ))

        moved = 0
        for member in members:
            try:
                await member.move_to(to_channel, reason=f"mass move by {ctx.author}")
                moved += 1
            except discord.Forbidden:
                continue

        await ctx.send(embed=discord.Embed(
            description=f"√ moved **{moved}** member(s) from {from_channel.mention} to {to_channel.mention}",
            color=0x57f287
        ))

async def setup(bot) -> None:
    await bot.add_cog(Move(bot))
