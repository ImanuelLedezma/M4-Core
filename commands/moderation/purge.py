import discord
import asyncio
import os
from datetime import datetime, timedelta, timezone
from discord.ext import commands
from helpers.logging import init as init_logging

_log = init_logging("purge")
MAX_BATCH = 100
DISCORD_OLD_DAYS = 14

class Purge(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="purge", aliases=["clear"], description="bulk delete messages", help="Delete messages in bulk. Optionally target a specific user: !purge 50 @user. Max 1000 messages. Only messages under 14 days old can be deleted. Requires Manage Messages permission.")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int, member: discord.Member = None):
        if amount < 1:
            return await ctx.send(embed=discord.Embed(
                title="✖ invalid amount",
                description="specify a number greater than 0.",
                color=discord.Color.red()
            ))

        amount = min(amount, 1000)

        try:
            retrieved = []
            cutoff = discord.utils.utcnow() - timedelta(days=DISCORD_OLD_DAYS)

            fetch_limit = amount if not member else amount * 5
            async for message in ctx.channel.history(limit=fetch_limit):
                if message.created_at < cutoff:
                    break
                if member and message.author != member:
                    continue
                retrieved.append(message)
                if len(retrieved) >= amount:
                    break

            if not retrieved:
                return await ctx.send(embed=discord.Embed(
                    description="no messages found to purge.",
                    color=0xff4500
                ), delete_after=5)

            confirm_msg = await ctx.send(embed=discord.Embed(
                description=f"⧖ purging `{len(retrieved)}` messages...",
                color=0x2b2d31
            ))

            self.log_to_file(ctx.guild.name, ctx.channel.name, retrieved)

            for i in range(0, len(retrieved), MAX_BATCH):
                batch = retrieved[i:i + MAX_BATCH]
                await ctx.channel.delete_messages(batch)
                await asyncio.sleep(0.5)

            await confirm_msg.edit(embed=discord.Embed(
                title="√ purged",
                description=f"cleaned `{len(retrieved)}` messages.",
                color=discord.Color.green()
            ))
            await asyncio.sleep(3)
            await confirm_msg.delete()

        except discord.Forbidden:
            await ctx.send(embed=discord.Embed(
                description="⊘ i need `manage_messages` permission to purge.",
                color=0xff4500
            ), delete_after=5)
        except discord.HTTPException as e:
            _log.error("purge error: %s", e)
            await ctx.send(embed=discord.Embed(
                description=f"✖ purge failed: {e}",
                color=0xff4500
            ), delete_after=5)

    def log_to_file(self, guild_name: str, channel_name: str, messages: list) -> None:
        log_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "logs"))
        os.makedirs(log_dir, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(log_dir, f"purge_{timestamp}.txt")

        with open(filename, "w", encoding="utf-8") as f:
            f.write("--- purge log ---\n")
            f.write(f"guild: {guild_name} | channel: {channel_name}\n")
            f.write(f"timestamp: {timestamp}\n")
            f.write("-" * 30 + "\n\n")

            for msg in reversed(messages):
                t = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{t}] {msg.author} ({msg.author.id}): {msg.content}\n")
                if msg.attachments:
                    f.write(f"   files: {[a.url for a in msg.attachments]}\n")

async def setup(bot) -> None:
    await bot.add_cog(Purge(bot))