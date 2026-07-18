import discord
from discord.ext import commands
from helpers.config import load_config, save_config, get_channel_id

class HallOfFame(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.channel_id = get_channel_id("hall_of_fame")
        self._posted: set[int] = set()

    @commands.hybrid_command(name="hof", description="add a replied message to the hall of fame", help="Add a message to the Hall of Fame by replying to it. Shows message content, author, source channel, and a jump link. Supports images. Prevents duplicate entries. Requires Manage Messages permission.")
    @commands.has_permissions(manage_messages=True)
    async def hof(self, ctx):
        if not ctx.message.reference:
            return await ctx.send(embed=discord.Embed(
                description="✖ you must reply to a message to add it to the hall of fame",
                color=0xff4500
            ), delete_after=5)

        try:
            ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        except discord.NotFound:
            return await ctx.send(embed=discord.Embed(
                description="✖ couldn't find the referenced message!", color=0xff4500
            ), delete_after=5)

        if ref_msg.id in self._posted:
            return await ctx.send(embed=discord.Embed(
                description="✖ that message is already in the hall of fame.",
                color=0xff4500
            ), delete_after=5)

        hof_channel = ctx.guild.get_channel(self.channel_id)
        if not hof_channel:
            return await ctx.send(embed=discord.Embed(
                description="✖ hall of fame channel not found!", color=0xff4500
            ), delete_after=5)

        self._posted.add(ref_msg.id)

        author = ref_msg.author
        embed = discord.Embed(
            description=ref_msg.content or None,
            color=0xf1c40f,
            timestamp=ref_msg.created_at
        )
        embed.set_author(name=author.display_name, icon_url=author.display_avatar.url)
        embed.add_field(name="source", value=f"[jump to message]({ref_msg.jump_url})", inline=True)
        embed.add_field(name="channel", value=ref_msg.channel.mention, inline=True)
        embed.set_footer(text=f"nominated by {ctx.author.display_name}")

        if ref_msg.attachments:
            first = ref_msg.attachments[0]
            if first.content_type and first.content_type.startswith("image"):
                embed.set_image(url=first.url)
            else:
                embed.add_field(name="attachment", value=f"[{first.filename}]({first.url})", inline=False)

        await hof_channel.send(embed=embed)
        await ctx.send(embed=discord.Embed(
            description=f"√ added to {hof_channel.mention}!",
            color=0x57f287
        ), delete_after=5)

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            await ctx.message.add_reaction("✅")

    @commands.hybrid_command(name="sethof", description="set the hall of fame channel", help="Set the channel where Hall of Fame entries are posted. Requires Manage Guild permission.")
    @commands.has_permissions(manage_guild=True)
    async def set_hof(self, ctx, channel: discord.TextChannel):
        cfg = load_config()
        cfg["channels"]["hall_of_fame"] = channel.id
        save_config(cfg)
        self.channel_id = channel.id
        await ctx.send(embed=discord.Embed(
            description=f"√ hall of fame channel set to {channel.mention}",
            color=0x57f287
        ))

async def setup(bot) -> None:
    await bot.add_cog(HallOfFame(bot))