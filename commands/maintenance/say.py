import discord
from discord.ext import commands
from helpers.admins_config import is_admin

class Say(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="say", description="send a message as the bot", help="Send a plain text message as the bot. The command message is deleted if possible. Admin only.")
    async def say(self, ctx, *, message: str):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized.", color=0xff4500))

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        await ctx.send(message)

    @commands.hybrid_command(name="embed", description="send an embed as the bot", help="Send an embedded message as the bot. Accepts raw JSON (discord embed format) or plain text. Admin only.")
    async def embed_say(self, ctx, *, json_or_text: str):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized.", color=0xff4500))

        try:
            import json
            data = json.loads(json_or_text)
            embed = discord.Embed.from_dict(data)
            await ctx.send(embed=embed)
        except Exception:
            embed = discord.Embed(description=json_or_text, color=0x2b2d31)
            await ctx.send(embed=embed)

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

    @commands.hybrid_command(name="edit", description="edit a message by id", help="Edit any message by its ID in the current channel. Admin only.")
    async def edit_msg(self, ctx, message_id: str, *, new_content: str):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized.", color=0xff4500))

        try:
            mid = int(message_id)
            msg = await ctx.channel.fetch_message(mid)
            await msg.edit(content=new_content)
            await ctx.message.add_reaction("✅")
        except (ValueError, discord.NotFound, discord.Forbidden) as e:
            await ctx.send(embed=discord.Embed(
                description=f"⊘ {e}", color=0xff4500
            ))

async def setup(bot) -> None:
    await bot.add_cog(Say(bot))