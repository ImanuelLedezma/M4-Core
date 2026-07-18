import time
import discord
from discord.ext import commands
from helpers.config import load_config, save_config, get_channel_id

COOLDOWN_SECONDS = 60

class Confessions(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.channel_id = get_channel_id("confession")
        self._cooldowns: dict[int, float] = {}

    @commands.hybrid_command(name="confess", description="send an anonymous confession (use in dms)", help="Send an anonymous confession to the configured confessions channel. Must be used in DMs with the bot. Supports image attachments. 60s cooldown.")
    async def confess(self, ctx, *, message: str):
        if ctx.guild is not None:
            return await ctx.send(embed=discord.Embed(
                description="⊘ use this command in dms for anonymity.",
                color=0x2b2d31
            ), delete_after=5)

        now = time.time()
        if ctx.author.id in self._cooldowns:
            remaining = COOLDOWN_SECONDS - (now - self._cooldowns[ctx.author.id])
            if remaining > 0:
                return await ctx.send(embed=discord.Embed(
                    description=f"⊘ please wait `{int(remaining)}s` before confessing again.",
                    color=0xff4500
                ), delete_after=5)
        self._cooldowns[ctx.author.id] = now

        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(self.channel_id)
            except (discord.Forbidden, discord.NotFound):
                return await ctx.send(embed=discord.Embed(
                    description="⊘ confession channel not found.",
                    color=0x2b2d31
                ))

        embed = discord.Embed(
            title="╼ anonymous confession ╾",
            description=message[:2000],
            color=0x2b2d31
        )
        embed.set_footer(text="use !confess in dms to share")

        if ctx.message.attachments:
            for att in ctx.message.attachments:
                if att.content_type and att.content_type.startswith("image"):
                    embed.set_image(url=att.url)
                else:
                    embed.add_field(name="attachment", value=f"[{att.filename}]({att.url})", inline=False)

        await channel.send(embed=embed)
        try:
            await ctx.author.send(embed=discord.Embed(
                description="◈ confession sent successfully.",
                color=0x2b2d31
            ), delete_after=5)
        except discord.Forbidden:
            pass

    @commands.hybrid_command(name="setconfessions", description="set the confessions channel", help="Set the channel where anonymous confessions are posted. Requires Manage Guild permission.")
    @commands.has_permissions(manage_guild=True)
    async def set_confessions(self, ctx, channel: discord.TextChannel):
        cfg = load_config()
        cfg["channels"]["confession"] = channel.id
        save_config(cfg)
        self.channel_id = channel.id
        await ctx.send(embed=discord.Embed(
            description=f"√ confessions channel set to {channel.mention}.",
            color=0x57f287
        ))

async def setup(bot) -> None:
    await bot.add_cog(Confessions(bot))