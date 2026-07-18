import discord
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType
from helpers.economy_base import load_bank, open_account
from helpers.config import get_config
from helpers.database import warn_count

EXCLUDED_ROLE = get_config("userinfo.excluded_role", 1489622224267641043)

class UserInfo(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="userinfo", aliases=["ui", "whois", "profile"], description="show detailed member information", help="Shows detailed user info: ID, status, badges, top role, nickname, join dates, warnings, economy stats (wallet/bank/debt/net worth), and role list.")
    @cooldown(1, 3, BucketType.user)
    async def userinfo(self, ctx, member: discord.Member = None):
        member = member or ctx.author

        joined_at = member.joined_at.strftime("%b %d, %Y %H:%M") if member.joined_at else "unknown"
        created_at = member.created_at.strftime("%b %d, %Y %H:%M")

        roles = [
            role.mention for role in reversed(member.roles)
            if role != ctx.guild.default_role and role.id != EXCLUDED_ROLE
        ]
        top_role = member.top_role.mention if member.top_role != ctx.guild.default_role else "none"

        badges = []
        if member.bot:
            badges.append("🤖 bot")
        if member.guild_permissions.administrator:
            badges.append("🛡 admin")
        if member.guild_permissions.manage_guild:
            badges.append("⚙ mod")
        if member.premium_since:
            badges.append("🌟 booster")
        if member.public_flags.verified_bot_developer:
            badges.append("👨‍💻 dev")

        status_icon = {"online": "🟢", "idle": "🟡", "dnd": "🔴", "offline": "⚫"}
        status = status_icon.get(str(member.status), "⚪")

        # economy
        data = load_bank()
        data = open_account(member.id, data)
        uid = str(member.id)
        wallet = data[uid]["wallet"]
        bank = data[uid]["bank"]
        debt = data[uid]["debt"]
        net = wallet + bank - debt

        # warnings
        wc = warn_count(ctx.guild.id, member.id)

        color = member.color if member.color.value else 0x2b2d31
        embed = discord.Embed(
            title=f"{status} {member.name}",
            description=" · ".join(badges) if badges else None,
            color=color
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(name="id", value=f"`{member.id}`", inline=True)
        embed.add_field(name="top role", value=top_role, inline=True)
        embed.add_field(name="nickname", value=member.nick or "none", inline=True)

        embed.add_field(name="joined server", value=joined_at, inline=True)
        embed.add_field(name="joined discord", value=created_at, inline=True)
        embed.add_field(name="warnings", value=f"`{wc}`", inline=True)

        embed.add_field(name="◈ wallet", value=f"⌬ {wallet:,}", inline=True)
        embed.add_field(name="◈ bank", value=f"⌬ {bank:,}", inline=True)
        if debt > 0:
            embed.add_field(name="⊘ debt", value=f"⌬ {debt:,}", inline=True)
        embed.add_field(name="▼ net worth", value=f"⌬ {net:,}", inline=False)

        if roles:
            role_str = " ".join(roles)
            if len(role_str) > 1024:
                role_str = role_str[:1020] + "..."
            embed.add_field(name=f"roles [{len(roles)}]", value=role_str, inline=False)

        embed.set_footer(text=f"requested by {ctx.author.name}")
        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(UserInfo(bot))