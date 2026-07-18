import discord
from discord.ext import commands

class Lockdown(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self._locked: set[int] = set()

    @commands.hybrid_command(name="lockdown", description="lock or unlock all channels in the server", help="Lock or unlock all text channels. When locked, @everyone can't send messages. Use !lockdown to toggle or !lockdown on/off to set. Requires Manage Channels permission.")
    @commands.has_permissions(manage_channels=True)
    async def lockdown(self, ctx, state: str = None):
        guild = ctx.guild
        everyone = guild.default_role

        if state and state.lower() in ("on", "enable", "lock"):
            lock = True
        elif state and state.lower() in ("off", "disable", "unlock"):
            lock = False
        else:
            lock = not self._locked

        self._locked.clear()
        if lock:
            self._locked.add(guild.id)

        changed = 0
        for channel in guild.text_channels:
            overwrite = channel.overwrites_for(everyone)
            if lock:
                if overwrite.send_messages is False:
                    continue
                overwrite.send_messages = False
            else:
                if overwrite.send_messages is None or overwrite.send_messages is True:
                    continue
                overwrite.send_messages = None
            try:
                await channel.set_permissions(everyone, overwrite=overwrite, reason=f"server {'lockdown' if lock else 'unlock'} by {ctx.author}")
                changed += 1
            except discord.Forbidden:
                continue

        status = "locked" if lock else "unlocked"
        await ctx.send(embed=discord.Embed(
            description=f"√ server {status} (**{changed}** channels affected)",
            color=0x57f287 if not lock else 0xff4500
        ))

async def setup(bot) -> None:
    await bot.add_cog(Lockdown(bot))
