import discord
from collections import defaultdict, deque
from discord.ext import commands

MAX_SNIPED = 20

class Snipe(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.sniped: dict[int, deque[dict]] = defaultdict(lambda: deque(maxlen=MAX_SNIPED))
        self.edits: dict[int, deque[dict]] = defaultdict(lambda: deque(maxlen=MAX_SNIPED))

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        self.sniped[message.channel.id].append({
            "content": message.content,
            "author": message.author,
            "avatar": message.author.display_avatar.url,
            "at": discord.utils.utcnow(),
            "attachments": message.attachments,
        })

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return
        self.edits[before.channel.id].append({
            "before": before.content,
            "after": after.content,
            "author": before.author,
            "avatar": before.author.display_avatar.url,
            "at": discord.utils.utcnow(),
        })

    @commands.hybrid_command(name="snipe", aliases=["s"], description="show the last deleted message", help="Show recently deleted messages in the current channel. Use !snipe 2 for older messages. Stores up to 20 deleted messages per channel.")
    async def snipe(self, ctx, index: int = 1):
        data = self.sniped.get(ctx.channel.id)
        if not data:
            return await ctx.send(embed=discord.Embed(
                title="⊘ nothing to snipe",
                description="no recently deleted messages in this channel.",
                color=0xff4500
            ))
        if index < 1 or index > len(data):
            return await ctx.send(embed=discord.Embed(
                description=f"⊘ use an index between `1` and `{len(data)}` (use `!snipe 2` for older)",
                color=0xff4500
            ))

        entry = data[-index]
        embed = discord.Embed(
            title=f"⌖ sniped ({index}/{len(data)})",
            description=entry["content"] or "*[no text content]*",
            color=0x5865f2
        )
        embed.set_author(name=entry["author"].display_name, icon_url=entry["avatar"])
        embed.set_footer(text=f"deleted at {entry['at'].strftime('%H:%M:%S')} UTC")
        if entry.get("attachments"):
            embed.add_field(name="attachments", value=str(len(entry["attachments"])), inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="editsnipe", aliases=["es"], description="show the last edited message", help="Show recently edited messages with before/after content. Use !es 2 for older edits.")
    async def editsnipe(self, ctx, index: int = 1):
        data = self.edits.get(ctx.channel.id)
        if not data:
            return await ctx.send(embed=discord.Embed(
                description="no edited messages in this channel.",
                color=0xff4500
            ))
        if index < 1 or index > len(data):
            return await ctx.send(embed=discord.Embed(
                description=f"⊘ use an index between `1` and `{len(data)}`",
                color=0xff4500
            ))

        entry = data[-index]
        embed = discord.Embed(
            title=f"✏ editsniped ({index}/{len(data)})",
            color=0xf1c40f
        )
        embed.set_author(name=entry["author"].display_name, icon_url=entry["avatar"])
        embed.add_field(name="before", value=entry["before"] or "*[empty]*", inline=False)
        embed.add_field(name="after", value=entry["after"] or "*[empty]*", inline=False)
        embed.set_footer(text=f"edited at {entry['at'].strftime('%H:%M:%S')} UTC")
        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Snipe(bot))