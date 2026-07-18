import discord
from discord.ext import commands
from helpers.economy_base import load_bank, save_bank, open_account, apply_earnings
from helpers.admins_config import is_admin
from helpers.database import codes_get, codes_set, codes_use, codes_delete, codes_all

class Codes(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="issuecode", description="create a redeemable code (admin)", help="Create a redeemable code with a core amount and usage limit. Admin only.")
    async def issuecode(self, ctx, code: str, amount: int, uses: int = 1000):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized", color=0xff4500))
        if amount <= 0:
            return await ctx.send(embed=discord.Embed(description="⊘ amount must be positive", color=0xff4500))

        code_key = code.upper()
        if codes_get(code_key):
            return await ctx.send(embed=discord.Embed(
                description=f"⊘ code `{code_key}` already exists!", color=0xff4500
            ))

        codes_set(code_key, amount, uses, ctx.author.id)
        await ctx.send(embed=discord.Embed(
            description=f"√ code `{code_key}` issued -- **⌬ {amount:,}** cores, **{uses}** use(s)",
            color=0x57f287
        ))

    @commands.hybrid_command(name="redeem", description="redeem a code for cores", help="Redeem a code to add cores to your wallet. Codes are case-insensitive. Each code has limited uses.")
    async def redeem(self, ctx, code: str):
        code_key = code.upper()
        entry = codes_get(code_key)
        if not entry:
            return await ctx.send(embed=discord.Embed(
                description="⊘ invalid code!", color=0xff4500
            ), ephemeral=True)

        if not codes_use(code_key):
            return await ctx.send(embed=discord.Embed(
                description="⊘ this code has no uses remaining.", color=0xff4500
            ), ephemeral=True)

        data = load_bank()
        data = open_account(ctx.author.id, data)
        amount = entry["amount"]
        debt_paid, _ = apply_earnings(str(ctx.author.id), data, amount)
        save_bank(data)

        desc = f"√ redeemed `{code_key}` -- **⌬ {amount:,}** cores added"
        if debt_paid:
            desc += f"\n⌬ {debt_paid:,} went toward your debt"

        await ctx.send(embed=discord.Embed(description=desc, color=0x57f287))

    @commands.hybrid_command(name="codeinfo", description="check code details (admin only)", help="Shows amount, remaining uses, and total redemptions. Admin only.")
    async def codeinfo(self, ctx, code: str):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized", color=0xff4500))

        entry = codes_get(code.upper())
        if not entry:
            return await ctx.send(embed=discord.Embed(
                description=f"⊘ code `{code.upper()}` doesn't exist.", color=0xff4500
            ))

        remaining = entry["max_uses"] - entry["uses"]
        embed = discord.Embed(title=f"code info · {code.upper()}", color=0x2b2d31)
        embed.add_field(name="amount", value=f"⌬ {entry['amount']:,}", inline=True)
        embed.add_field(name="uses remaining", value=str(remaining), inline=True)
        embed.add_field(name="total redeemed", value=str(entry["uses"]), inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="revokecode", description="delete a redeemable code (admin)", help="Permanently delete a code. Admin only.")
    async def revokecode(self, ctx, code: str):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized", color=0xff4500))

        code_key = code.upper()
        if not codes_get(code_key):
            return await ctx.send(embed=discord.Embed(
                description=f"⊘ code `{code_key}` doesn't exist!", color=0xff4500
            ))

        codes_delete(code_key)
        await ctx.send(embed=discord.Embed(
            description=f"√ code `{code_key}` revoked", color=0x57f287
        ))

    @commands.hybrid_command(name="codelist", description="list all active codes (admin only)", help="Lists every redeemable code with amount, uses left, and redemption count. Admin only.")
    async def codelist(self, ctx):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized", color=0xff4500))

        codes = codes_all()
        if not codes:
            return await ctx.send(embed=discord.Embed(description="no codes exist.", color=0x2b2d31))

        lines = []
        for key, entry in sorted(codes.items()):
            remaining = entry["max_uses"] - entry["uses"]
            lines.append(f"`{key}` · ⌬ {entry['amount']:,} · {remaining} uses · {entry['uses']} redeemed")

        await ctx.send(embed=discord.Embed(
            title=f"codes ({len(codes)})",
            description="\n".join(lines),
            color=0x2b2d31
        ))

async def setup(bot) -> None:
    await bot.add_cog(Codes(bot))
