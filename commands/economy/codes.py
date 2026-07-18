import discord
from discord.ext import commands
from helpers.economy_base import load_bank, save_bank, open_account, apply_earnings
from helpers.admins_config import is_admin
from helpers.storage import load, save

CODES_FILE = "codes.msgpack"

def load_codes():
    return load(CODES_FILE)

def save_codes(data):
    save(CODES_FILE, data)

class Codes(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="issuecode", description="create a redeemable code (admin)", help="Create a redeemable code with a core amount and usage limit. Admin only.")
    async def issuecode(self, ctx, code: str, amount: int, uses: int = 1000):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized", color=0xff4500))
        if amount <= 0:
            return await ctx.send(embed=discord.Embed(description="⊘ amount must be positive", color=0xff4500))

        codes = load_codes()
        code = code.upper()
        if code in codes:
            return await ctx.send(embed=discord.Embed(
                description=f"⊘ code `{code}` already exists!", color=0xff4500
            ))

        codes[code] = {"amount": amount, "uses": uses, "redeemed_by": []}
        save_codes(codes)

        await ctx.send(embed=discord.Embed(
            description=f"√ code `{code}` issued — **⌬ {amount:,}** cores, **{uses}** use(s)",
            color=0x57f287
        ))

    @commands.hybrid_command(name="redeem", description="redeem a code for cores", help="Redeem a code to add cores to your wallet. Codes are case-insensitive. Each code can only be redeemed once per user.")
    async def redeem(self, ctx, code: str):
        codes = load_codes()
        code = code.upper()

        if code not in codes:
            return await ctx.send(embed=discord.Embed(
                description="⊘ invalid code!", color=0xff4500
            ), ephemeral=True)

        entry = codes[code]
        uid = str(ctx.author.id)

        if uid in entry["redeemed_by"]:
            return await ctx.send(embed=discord.Embed(
                description="⊘ you've already redeemed this code!", color=0xff4500
            ), ephemeral=True)
        if entry["uses"] <= 0:
            return await ctx.send(embed=discord.Embed(
                description="⊘ this code has no uses remaining..", color=0xff4500
            ), ephemeral=True)

        entry["redeemed_by"].append(uid)
        entry["uses"] -= 1
        save_codes(codes)

        data = load_bank()
        data = open_account(ctx.author.id, data)
        amount = entry["amount"]
        debt_paid, _ = apply_earnings(uid, data, amount)
        save_bank(data)

        desc = f"√ redeemed `{code}` — **⌬ {amount:,}** cores added"
        if debt_paid:
            desc += f"\n⌬ {debt_paid:,} went toward your debt"

        await ctx.send(embed=discord.Embed(description=desc, color=0x57f287))

    @commands.hybrid_command(name="codeinfo", description="check code details (admin only)", help="Shows amount, remaining uses, total redemptions, and expiry for a code. Admin only.")
    async def codeinfo(self, ctx, code: str):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized", color=0xff4500))

        codes = load_codes()
        code = code.upper()
        if code not in codes:
            return await ctx.send(embed=discord.Embed(
                description=f"⊘ code `{code}` doesn't exist.", color=0xff4500
            ))

        entry = codes[code]
        embed = discord.Embed(title=f"code info · {code}", color=0x2b2d31)
        embed.add_field(name="amount", value=f"⌬ {entry['amount']:,}", inline=True)
        embed.add_field(name="uses remaining", value=str(entry["uses"]), inline=True)
        embed.add_field(name="total redeemed", value=str(len(entry["redeemed_by"])), inline=True)
        if entry.get("expires_at"):
            embed.add_field(name="expires", value=f"<t:{int(entry['expires_at'])}:R>", inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="revokecode", description="delete a redeemable code (admin)", help="Permanently delete a code. Admin only.")
    async def revokecode(self, ctx, code: str):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized", color=0xff4500))

        codes = load_codes()
        code = code.upper()
        if code not in codes:
            return await ctx.send(embed=discord.Embed(
                description=f"⊘ code `{code}` doesn't exist!", color=0xff4500
            ))

        del codes[code]
        save_codes(codes)
        await ctx.send(embed=discord.Embed(
            description=f"√ code `{code}` revoked", color=0x57f287
        ))

    @commands.hybrid_command(name="codelist", description="list all active codes (admin only)", help="Lists every redeemable code with amount, uses left, and redemption count. Admin only.")
    async def codelist(self, ctx):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized", color=0xff4500))

        codes = load_codes()
        if not codes:
            return await ctx.send(embed=discord.Embed(description="no codes exist.", color=0x2b2d31))

        lines = []
        for code, entry in sorted(codes.items()):
            lines.append(f"`{code}` · ⌬ {entry['amount']:,} · {entry['uses']} uses · {len(entry['redeemed_by'])} redeemed")

        await ctx.send(embed=discord.Embed(
            title=f"codes ({len(codes)})",
            description="\n".join(lines),
            color=0x2b2d31
        ))

async def setup(bot) -> None:
    await bot.add_cog(Codes(bot))