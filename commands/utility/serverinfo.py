import discord
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType

class ServerInfo(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="serverinfo", aliases=["si", "server"], description="show detailed guild information", help="Shows detailed server information: owner, creation date, member count (humans/bots), channels (text/voice/forum/categories), roles, emojis, stickers, boost level, verification level, AFK channel.")
    @cooldown(1, 3, BucketType.user)
    async def serverinfo(self, ctx):
        guild = ctx.guild
        created_at = guild.created_at.strftime("%b %d, %Y")

        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        forum_channels = len(guild.forum_channels)
        categories = len(guild.categories)
        roles = len(guild.roles) - 1

        bots = sum(1 for m in guild.members if m.bot)
        humans = guild.member_count - bots

        boost_level = guild.premium_tier
        boosts = guild.premium_subscription_count
        boosters = len(guild.premium_subscribers)

        emojis = len(guild.emojis)
        stickers = len(guild.stickers)
        afk_channel = guild.afk_channel.mention if guild.afk_channel else "none"
        verif = str(guild.verification_level).title()

        embed = discord.Embed(
            title=guild.name,
            description=guild.description or "no description set.",
            color=0x5865f2
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        if guild.banner:
            embed.set_image(url=guild.banner.url)

        embed.add_field(name="owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="id", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="created", value=created_at, inline=True)

        embed.add_field(name="members", value=f"total `{guild.member_count}` · humans `{humans}` · bots `{bots}`", inline=False)
        embed.add_field(name="channels", value=f"text `{text_channels}` · voice `{voice_channels}` · forum `{forum_channels}` · categories `{categories}`", inline=False)
        embed.add_field(name="other", value=f"roles `{roles}` · emojis `{emojis}` · stickers `{stickers}`", inline=False)
        embed.add_field(name="boosts", value=f"level `{boost_level}` · `{boosts}` boosts · `{boosters}` boosters", inline=False)
        embed.add_field(name="verification", value=verif, inline=True)
        embed.add_field(name="afk channel", value=afk_channel, inline=True)

        embed.set_footer(text=f"requested by {ctx.author.name}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="channelinfo", aliases=["ci", "channel"], description="show channel details", help="Shows detailed information about the current or mentioned channel: type, topic, position, creation date, slowmode, NSFW status, and category.")
    async def channelinfo(self, ctx, *, channel: discord.TextChannel | discord.VoiceChannel | discord.ForumChannel = None):
        channel = channel or ctx.channel
        created = channel.created_at.strftime("%b %d, %Y")

        embed = discord.Embed(title=f"# {channel.name}", color=0x2b2d31)

        if isinstance(channel, discord.TextChannel):
            embed.add_field(name="type", value="text", inline=True)
            embed.add_field(name="topic", value=channel.topic or "none", inline=False)
            embed.add_field(name="slowmode", value=f"{channel.slowmode_delay}s" if channel.slowmode_delay else "off", inline=True)
            embed.add_field(name="nsfw", value="✅" if channel.nsfw else "❌", inline=True)
            embed.add_field(name="position", value=f"`{channel.position}`", inline=True)
            embed.add_field(name="category", value=channel.category.name if channel.category else "none", inline=True)
            if channel.last_message_id:
                try:
                    last = await channel.fetch_message(channel.last_message_id)
                    embed.add_field(name="last message", value=f"{last.author.display_name} — {last.created_at.strftime('%b %d, %Y')}", inline=False)
                except (discord.NotFound, discord.Forbidden):
                    pass
        elif isinstance(channel, discord.VoiceChannel):
            embed.add_field(name="type", value="voice", inline=True)
            embed.add_field(name="bitrate", value=f"{channel.bitrate // 1000}kbps", inline=True)
            embed.add_field(name="user limit", value=channel.user_limit or "unlimited", inline=True)
            embed.add_field(name="position", value=f"`{channel.position}`", inline=True)
            embed.add_field(name="category", value=channel.category.name if channel.category else "none", inline=True)
        elif isinstance(channel, discord.ForumChannel):
            embed.add_field(name="type", value="forum", inline=True)
            embed.add_field(name="topic", value=channel.topic or "none", inline=False)
            embed.add_field(name="position", value=f"`{channel.position}`", inline=True)

        embed.add_field(name="id", value=f"`{channel.id}`", inline=True)
        embed.add_field(name="created", value=created, inline=True)
        embed.set_footer(text=f"requested by {ctx.author.name}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="roles", aliases=["rolelist"], description="list all server roles", help="Shows all roles in the server with member counts and color indicators.")
    async def roles(self, ctx):
        roles = sorted([r for r in ctx.guild.roles if not r.is_default()], key=lambda r: r.position, reverse=True)
        if not roles:
            return await ctx.send(embed=discord.Embed(description="no roles in this server.", color=0x2b2d31))

        chunks = [roles[i:i + 30] for i in range(0, len(roles), 30)]
        for chunk in chunks:
            embed = discord.Embed(title=f"roles ({len(roles)} total)", color=0x2b2d31)
            for role in chunk:
                embed.add_field(
                    name=f"{role.mention}",
                    value=f"`{len(role.members)}` members · `{role.id}`",
                    inline=True
                )
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="serveravatar", aliases=["guildicon", "servericon", "sicon"], description="show the server icon", help="Shows the server's icon/avatar in full size.")
    async def serveravatar(self, ctx):
        if not ctx.guild.icon:
            return await ctx.send(embed=discord.Embed(description="this server has no icon.", color=0x2b2d31))
        embed = discord.Embed(title=f"{ctx.guild.name}'s icon", color=0x2b2d31)
        embed.set_image(url=ctx.guild.icon.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="emojis", aliases=["serveremojis"], description="list all server emojis", help="Shows all custom emojis in the server with their names.")
    async def emojis(self, ctx):
        if not ctx.guild.emojis:
            return await ctx.send(embed=discord.Embed(description="no custom emojis in this server.", color=0x2b2d31))

        static = [e for e in ctx.guild.emojis if not e.animated]
        animated = [e for e in ctx.guild.emojis if e.animated]

        embed = discord.Embed(title=f"emojis ({len(ctx.guild.emojis)} total)", color=0x2b2d31)
        if static:
            embed.add_field(name=f"static ({len(static)})", value=" ".join(str(e) for e in static[:50]), inline=False)
        if animated:
            embed.add_field(name=f"animated ({len(animated)})", value=" ".join(str(e) for e in animated[:50]), inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="boosters", aliases=["boosts", "boostlist"], description="show server boost status", help="Shows boost level, boost count, and list of active boosters.")
    async def boosters(self, ctx):
        guild = ctx.guild
        boosters = guild.premium_subscribers
        embed = discord.Embed(title="boost status", color=0x5865f2)
        embed.add_field(name="level", value=f"`{guild.premium_tier}`", inline=True)
        embed.add_field(name="boosts", value=f"`{guild.premium_subscription_count}`", inline=True)
        embed.add_field(name="boosters", value=f"`{len(boosters)}`", inline=True)
        if guild.premium_tier > 0:
            perks = []
            if guild.premium_tier >= 1:
                perks.append("128kbps audio, 50 emoji slots, animated icon")
            if guild.premium_tier >= 2:
                perks.append("256kbps audio, 150 emoji, 1080p streaming, upload limit 50mb")
            if guild.premium_tier >= 3:
                perks.append("384kbps audio, 250 emoji, 4k streaming, upload limit 500mb, animated banner")
            embed.add_field(name="perks", value="\n".join(f"• {p}" for p in perks), inline=False)
        if boosters:
            names = "\n".join(b.display_name for b in boosters[:20])
            embed.add_field(name=f"boosters ({len(boosters)})", value=names[:1024], inline=False)
        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(ServerInfo(bot))