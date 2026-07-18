import discord
import aiohttp
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType
from helpers.config import load_config, save_config, get_channel_id

ALLOWED_CHANNEL = get_channel_id("dictionary")

class Dictionary(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self._session = None
        self._cache: dict[str, list] = {}

    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def cog_unload(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _define(self, term: str) -> list | None:
        if term in self._cache:
            return self._cache[term]
        session = await self._get_session()
        try:
            async with session.get(
                "https://api.urbandictionary.com/v0/define",
                params={"term": term}
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
        except (aiohttp.ClientError, ValueError, TypeError):
            return None
        results = data.get("list", [])
        self._cache[term] = results
        return results

    @commands.hybrid_command(name="dict", aliases=["dictionary", "define"], description="look up a term on urban dictionary", help="Look up a term on Urban Dictionary. Shows definition, example, and up/down votes. Results are cached. Restricted to the designated dictionary channel.")
    @cooldown(1, 3, BucketType.user)
    async def dict(self, ctx, *, term: str):
        channel_check = getattr(ctx, "channel_id_override", ctx.channel.id)
        if channel_check != ALLOWED_CHANNEL and not getattr(ctx, "bypass_channel", False):
            return await ctx.send(embed=discord.Embed(
                description="⊘ you can only use this in a designated dictionary channel.",
                color=0xff4500
            ), delete_after=5)

        results = await self._define(term)
        if results is None:
            return await ctx.send(embed=discord.Embed(
                description="✖ couldn't reach urban dictionary.", color=0xff4500
            ))
        if not results:
            return await ctx.send(embed=discord.Embed(
                description=f"✖ no results for **{term}**.", color=0xff4500
            ))

        top = results[0]
        definition = top["definition"].replace("[", "").replace("]", "")
        example = top["example"].replace("[", "").replace("]", "")

        if len(definition) > 1024:
            definition = definition[:1021] + "..."
        if len(example) > 512:
            example = example[:509] + "..."

        embed = discord.Embed(title=top["word"], url=top["permalink"], color=0x2b2d31)
        embed.add_field(name="◈ definition", value=definition or "*none*", inline=False)
        if example.strip():
            embed.add_field(name="◈ example", value=f"*{example}*", inline=False)
        embed.set_footer(text=f"👍 {top['thumbs_up']:,}  👎 {top['thumbs_down']:,} · urban dictionary")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="randict", aliases=["randomword", "randomdict"], description="get a random urban dictionary entry", help="Get a random entry from Urban Dictionary.")
    async def random_dict(self, ctx):
        session = await self._get_session()
        try:
            async with session.get("https://api.urbandictionary.com/v0/random") as resp:
                if resp.status != 200:
                    return await ctx.send(embed=discord.Embed(
                        description="✖ couldn't reach urban dictionary.", color=0xff4500
                    ))
                data = await resp.json()
        except (aiohttp.ClientError, ValueError, TypeError):
            return await ctx.send(embed=discord.Embed(
                description="✖ couldn't reach urban dictionary.", color=0xff4500
            ))
        results = data.get("list", [])
        if not results:
            return await ctx.send(embed=discord.Embed(description="✖ no results found.", color=0xff4500))

        entry = results[0]
        definition = entry["definition"].replace("[", "").replace("]", "")
        example = entry["example"].replace("[", "").replace("]", "")

        embed = discord.Embed(title=f"🎲 {entry['word']}", url=entry["permalink"], color=0x2b2d31)
        embed.add_field(name="◈ definition", value=definition[:1024] or "*none*", inline=False)
        if example.strip():
            embed.add_field(name="◈ example", value=f"*{example[:512]}*", inline=False)
        embed.set_footer(text=f"👍 {entry['thumbs_up']:,}  👎 {entry['thumbs_down']:,} · random entry")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="setdictionary", description="set the dictionary lookup channel")
    @commands.has_permissions(manage_guild=True)
    async def set_dictionary(self, ctx, channel: discord.TextChannel):
        global ALLOWED_CHANNEL
        cfg = load_config()
        cfg["channels"]["dictionary"] = channel.id
        save_config(cfg)
        ALLOWED_CHANNEL = channel.id
        await ctx.send(embed=discord.Embed(
            description=f"√ dictionary channel set to {channel.mention}.",
            color=0x57f287
        ))

async def setup(bot) -> None:
    await bot.add_cog(Dictionary(bot))