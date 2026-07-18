import discord
from discord.ext import commands
from helpers.economy_base import load_bank, save_bank, open_account, debt_prompt
from helpers.admins_config import is_admin
WALLET_FLOOR = 250

class Transfers(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.limit = 50000

    @commands.hybrid_command(name="deposit", aliases=["dep"], description="move cores to your bank", help="Move cores from your wallet to your bank. Keeps 250 cores in your wallet as a floor. Use !dep all to deposit everything above the floor.")
    async def deposit(self, ctx, amount: str):
        data = load_bank()
        data = open_account(ctx.author.id, data)
        user_id = str(ctx.author.id)

        data = await debt_prompt(ctx, self.bot, data, ctx.author.id)

        wallet = data[user_id]["wallet"]
        available = max(0, wallet - WALLET_FLOOR)

        if amount.lower() == "all":
            amount = available
        else:
            try:
                amount = int(amount)
            except ValueError:
                return await ctx.send(embed=discord.Embed(description="⊘ amount must be a number or `all`.", color=0xff4500))

        if amount <= 0:
            return await ctx.send(embed=discord.Embed(
                description=f"⊘ you must keep at least **⌬ {WALLET_FLOOR:,}** in your wallet!",
                color=0xff4500
            ))

        if amount > available:
            return await ctx.send(embed=discord.Embed(
                description=f"⊘ you can only deposit **⌬ {available:,}** — must keep **⌬ {WALLET_FLOOR:,}** in your wallet",
                color=0xff4500
            ))

        data[user_id]["wallet"] -= amount
        data[user_id]["bank"] += amount
        save_bank(data)
        await ctx.send(embed=discord.Embed(description=f"◈ deposited **⌬ {amount:,}** cores.", color=0x2b2d31))

    @commands.hybrid_command(name="withdraw", aliases=["with"], description="move cores to your wallet", help="Move cores from your bank back to your wallet. Use !with all to withdraw everything.")
    async def withdraw(self, ctx, amount: str):
        data = load_bank()
        data = open_account(ctx.author.id, data)
        user_id = str(ctx.author.id)

        data = await debt_prompt(ctx, self.bot, data, ctx.author.id)

        bank = data[user_id]["bank"]
        if amount.lower() == "all":
            amount = bank
        else:
            try:
                amount = int(amount)
            except ValueError:
                return await ctx.send(embed=discord.Embed(description="⊘ amount must be a number or `all`.", color=0xff4500))

        if amount > bank or amount <= 0:
            return await ctx.send(embed=discord.Embed(description="⊘ insufficient bank cores", color=0xff4500))

        data[user_id]["bank"] -= amount
        data[user_id]["wallet"] += amount
        save_bank(data)
        await ctx.send(embed=discord.Embed(description=f"◈ withdrew **⌬ {amount:,}** cores", color=0x2b2d31))

    @commands.hybrid_command(name="pay", description="transfer cores to another user", help="Send cores from your wallet to another user. Max 50,000 per transaction. You can't pay yourself.")
    async def pay(self, ctx, member: discord.Member, amount: int):
        if member.id == ctx.author.id:
            return await ctx.send("⊘ you cannot pay yourself!")

        if amount > self.limit:
            return await ctx.send(embed=discord.Embed(description=f"⊘ transfer limit is **⌬ {self.limit:,}**.", color=0xff4500))

        data = load_bank()
        data = open_account(ctx.author.id, data)
        data = open_account(member.id, data)

        data = await debt_prompt(ctx, self.bot, data, ctx.author.id)

        sender_id = str(ctx.author.id)
        rec_id = str(member.id)

        if amount <= 0 or amount > data[sender_id]["wallet"]:
            return await ctx.send(embed=discord.Embed(description="⊘ insufficient cores in wallet.", color=0xff4500))

        data[sender_id]["wallet"] -= amount
        data[rec_id]["wallet"] += amount
        save_bank(data)

        await ctx.send(embed=discord.Embed(
            description=f"╼ **transfer complete!** ╾\n\nsent **⌬ {amount:,}** to {member.display_name.lower()}",
            color=0x2b2d31
        ))

    @commands.group(name="sudo", invoke_without_command=True, help="Admin economy commands: transfer, deduct, set, wipe. Requires admin authorization.")
    async def sudo(self, ctx):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized.", color=0xff4500))
        await ctx.send(embed=discord.Embed(
            description="usage: `!sudo transfer/deduct/set/wipe`",
            color=0x2b2d31
        ))

    async def cog_check(self, ctx):
        if ctx.command and ctx.command.parent and ctx.command.parent.name == "sudo":
            if not is_admin(ctx.author.id):
                return False
        return True

    @sudo.command(name="transfer", help="Move cores between a user's wallet and bank accounts.")
    async def sudo_transfer(self, ctx, member: discord.Member, amount: int, account: str):
        account = account.lower()
        if account not in ("bank", "wallet"):
            return await ctx.send(embed=discord.Embed(description="⊘ account must be `bank` or `wallet`", color=0xff4500))

        data = load_bank()
        data = open_account(member.id, data)
        uid = str(member.id)

        if account == "bank":
            if data[uid]["wallet"] < amount:
                return await ctx.send(embed=discord.Embed(description="⊘ insufficient wallet cores", color=0xff4500))
            data[uid]["wallet"] -= amount
            data[uid]["bank"] += amount
            desc = f"◈ moved **⌬ {amount:,}** from {member.display_name.lower()}'s wallet → bank"
        else:
            if data[uid]["bank"] < amount:
                return await ctx.send(embed=discord.Embed(description="⊘ insufficient bank cores", color=0xff4500))
            data[uid]["bank"] -= amount
            data[uid]["wallet"] += amount
            desc = f"◈ moved **⌬ {amount:,}** from {member.display_name.lower()}'s bank → wallet"

        save_bank(data)
        await ctx.send(embed=discord.Embed(description=desc, color=0x57f287))

    @sudo.command(name="deduct", help="Remove cores from a user's wallet or bank account.")
    async def sudo_deduct(self, ctx, member: discord.Member, amount: int, account: str):
        account = account.lower()
        if account not in ("bank", "wallet"):
            return await ctx.send(embed=discord.Embed(description="⊘ account must be `bank` or `wallet`", color=0xff4500))

        data = load_bank()
        data = open_account(member.id, data)
        uid = str(member.id)

        current = data[uid][account]
        deducted = min(amount, current)
        data[uid][account] = max(0, current - amount)
        save_bank(data)

        await ctx.send(embed=discord.Embed(
            description=f"◈ deducted **⌬ {deducted:,}** from {member.display_name.lower()}'s {account}",
            color=0x57f287
        ))

    @sudo.command(name="set", help="Set a user's wallet or bank to a specific amount. Requires --force flag.")
    async def sudo_set(self, ctx, member: discord.Member, amount: int, account: str, flag: str = ""):
        if flag != "--force":
            return await ctx.send(embed=discord.Embed(
                description="⊘ append `--force` to confirm",
                color=0xff4500
            ))

        account = account.lower()
        if account not in ("bank", "wallet"):
            return await ctx.send(embed=discord.Embed(description="⊘ account must be `bank` or `wallet`", color=0xff4500))

        data = load_bank()
        data = open_account(member.id, data)
        uid = str(member.id)

        data[uid][account] = amount
        save_bank(data)

        await ctx.send(embed=discord.Embed(
            description=f"◈ set {member.display_name.lower()}'s {account} to **⌬ {amount:,}**",
            color=0x57f287
        ))

    @sudo.command(name="wipe", help="Delete all economy data for a user. Requires --force flag.")
    async def sudo_wipe(self, ctx, member: discord.Member, flag: str = ""):
        if flag != "--force":
            return await ctx.send(embed=discord.Embed(
                description=f"⊘ this will permanently delete all economy data for {member.display_name}. append `--force` to confirm",
                color=0xff4500
            ))

        data = load_bank()
        uid = str(member.id)

        if uid not in data:
            return await ctx.send(embed=discord.Embed(
                description="⊘ that user has no economy data!",
                color=0xff4500
            ))

        del data[uid]
        save_bank(data)

        await ctx.send(embed=discord.Embed(
            description=f"◈ wiped all economy data for {member.display_name.lower()}",
            color=0x57f287
        ))

async def setup(bot) -> None:
    await bot.add_cog(Transfers(bot))
