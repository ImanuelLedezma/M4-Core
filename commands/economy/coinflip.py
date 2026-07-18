import discord
import random
from discord.ext import commands
from helpers.economy_base import load_bank, save_bank, open_account, apply_loss, apply_earnings, debt_prompt
from commands.economy.shop import user_has_item

class Coinflip(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="coinflip", aliases=["cf"], description="bet cores on heads or tails", help="Bet cores on a coin flip. Choose heads or tails, win double your bet or lose it all. Tracks your wins/losses/net. Use !cfstats to see your record.")
    async def coinflip(self, ctx, side: str, amount: int):
        side = side.lower()
        if side not in ("heads", "tails", "h", "t"):
            return await ctx.send(embed=discord.Embed(
                description="✖ choose `heads` or `tails`",
                color=0xff4500
            ))

        side = "heads" if side in ("heads", "h") else "tails"

        if amount <= 0:
            return await ctx.send(embed=discord.Embed(
                description="⊘ bet must be greater than 0!",
                color=0xff4500
            ))

        data = load_bank()
        data = open_account(ctx.author.id, data)
        uid = str(ctx.author.id)

        data = await debt_prompt(ctx, self.bot, data, ctx.author.id)

        if amount > data[uid]["wallet"]:
            return await ctx.send(embed=discord.Embed(
                description="⊘ insufficient cores in wallet!",
                color=0xff4500
            ))

        has_socks = user_has_item(ctx.author.id, "lucky_socks")
        if has_socks:
            result = "heads" if random.random() < 0.55 else "tails"
        else:
            result = random.choice(["heads", "tails"])
        won = result == side
        coin = "🪙"
        stats = {
            "wins": data[uid].get("cf_wins", 0),
            "losses": data[uid].get("cf_losses", 0),
            "net": data[uid].get("cf_net", 0),
        }

        if won:
            debt_paid, to_wallet = apply_earnings(uid, data, amount)
            desc = f"{coin} **{result}** — you won **⌬ {amount:,}** cores"
            if debt_paid:
                desc += f"\n⌬ {debt_paid:,} went toward your debt"
            color = 0x57f287
            stats["wins"] += 1
            stats["net"] += amount
        else:
            apply_loss(uid, data, amount)
            debt = data[uid]["debt"]
            desc = f"{coin} **{result}** — you lost **⌬ {amount:,}** cores"
            if debt > 0:
                desc += f"\n⌬ {debt:,} now in debt"
            color = 0xff4500
            stats["losses"] += 1
            stats["net"] -= amount

        data[uid]["cf_wins"] = stats["wins"]
        data[uid]["cf_losses"] = stats["losses"]
        data[uid]["cf_net"] = stats["net"]
        save_bank(data)

        total = stats["wins"] + stats["losses"]
        winrate = f"{stats['wins']}/{total}" if total else "0/0"
        embed = discord.Embed(description=desc, color=color)
        embed.set_footer(text=f"wallet: {data[uid]['wallet']:,} cores · cf record: {winrate}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="cfstats", aliases=["coinflipstats"], description="check your coinflip statistics", help="Shows your total coinflip wins, losses, winrate percentage, and net cores won/lost.")
    async def cfstats(self, ctx):
        data = load_bank()
        data = open_account(ctx.author.id, data)
        uid = str(ctx.author.id)
        stats = {
            "wins": data[uid].get("cf_wins", 0),
            "losses": data[uid].get("cf_losses", 0),
            "net": data[uid].get("cf_net", 0),
        }
        total = stats["wins"] + stats["losses"]
        if not total:
            return await ctx.send(embed=discord.Embed(
                description="no coinflip history yet.",
                color=0x2b2d31
            ))
        winrate = round(stats["wins"] / total * 100, 1)
        embed = discord.Embed(title="coinflip stats", color=0x2b2d31)
        embed.add_field(name="wins", value=str(stats["wins"]), inline=True)
        embed.add_field(name="losses", value=str(stats["losses"]), inline=True)
        embed.add_field(name="winrate", value=f"{winrate}%", inline=True)
        embed.add_field(name="net", value=f"⌬ {stats['net']:,}", inline=True)
        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Coinflip(bot))