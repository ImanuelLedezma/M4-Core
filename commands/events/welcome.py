import discord
import random
from discord.ext import commands
from helpers.config import load_config, save_config

WELCOME_MESSAGES = [
    "glad to have you here, {mention}",
    "welcome to the server, {name}!",
    "a wild {name} appeared!",
    "{name} has joined the party!",
    "everyone welcome {mention}!",
    "fresh meat— i mean, welcome {name}!",
]

class Welcome(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.channel_id = load_config()["channels"].get("welcome")
        self.auto_role_id = load_config().get("welcome", {}).get("auto_role")

    @commands.hybrid_command(name="setwelcome", description="set the welcome channel", help="Set the channel where welcome messages are posted when new members join. Requires Manage Guild permission.")
    @commands.has_permissions(manage_guild=True)
    async def setwelcome(self, ctx, channel: discord.TextChannel):
        cfg = load_config()
        cfg["channels"]["welcome"] = channel.id
        save_config(cfg)
        self.channel_id = channel.id
        await ctx.send(embed=discord.Embed(
            title="√ welcome channel set",
            description=f"welcome messages will now be sent to {channel.mention}",
            color=discord.Color.green()
        ))

    @commands.hybrid_command(name="setautorole", description="set a role to auto-assign to new members", help="Set a role that will be automatically assigned to all new members when they join. Requires Manage Guild permission.")
    @commands.has_permissions(manage_guild=True)
    async def setautorole(self, ctx, role: discord.Role):
        cfg = load_config()
        if "welcome" not in cfg:
            cfg["welcome"] = {}
        cfg["welcome"]["auto_role"] = role.id
        save_config(cfg)
        self.auto_role_id = role.id
        await ctx.send(embed=discord.Embed(
            description=f"√ auto-role set to {role.mention}",
            color=0x57f287
        ))

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if self.auto_role_id:
            role = member.guild.get_role(self.auto_role_id)
            if role:
                try:
                    await member.add_roles(role, reason="auto-role on join")
                except discord.Forbidden:
                    pass

        if not self.channel_id:
            return
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            return

        msg = random.choice(WELCOME_MESSAGES).format(
            mention=member.mention,
            name=member.display_name,
        )

        embed = discord.Embed(
            title="welcome!",
            description=msg,
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"member #{member.guild.member_count}")
        await channel.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Welcome(bot))