import discord
import random
import asyncio
import os
from discord.ext import commands
from groq import Groq
from helpers.economy_base import load_bank, save_bank, open_account, apply_loss, apply_earnings, debt_prompt
from helpers.logging import init as init_logging

_log = init_logging("plinko")
ROWS = 6
SLOTS = ["▼", "◈", "❖", "▲", "✦"]
TOTAL_COLS = len(SLOTS) * 2 - 1

RISK_MODES = {
    "low": {"multipliers": [0.5, 0.8, 1.0, 1.2, 1.5], "weights": [10, 25, 30, 25, 10]},
    "medium": {"multipliers": [0.2, 0.5, 1.2, 1.5, 3.0], "weights": [25, 35, 20, 15, 5]},
    "high": {"multipliers": [0.0, 0.2, 1.5, 3.0, 5.0], "weights": [35, 30, 20, 10, 5]},
}

RISK_EMOJIS = {"🟢": "low", "🟡": "medium", "🔴": "high"}

def build_board(path, current_col, row):
    lines = []
    for r in range(ROWS):
        pegs = []
        for c in range(TOTAL_COLS):
            if r < row:
                if c == path[r]:
                    if r > 0:
                        prev = path[r - 1]
                        pegs.append("╲" if prev < c else "╱" if prev > c else "│")
                    else:
                        pegs.append("│")
                else:
                    pegs.append("·")
            elif r == row:
                pegs.append("⬤" if c == current_col else "·")
            else:
                pegs.append("·")
        lines.append("  ".join(pegs))
    width = TOTAL_COLS * 3 - 2
    lines.append("═" * width)
    gap = (width - len(SLOTS)) // (len(SLOTS) - 1)
    lines.append((" " * gap).join(SLOTS))
    return "\n".join(lines)

class Plinko(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self._groq = None

    def _get_groq(self):
        if self._groq is None:
            api_key = os.getenv("GROQ_KEY")
            if api_key:
                self._groq = Groq(api_key=api_key)
        return self._groq

    def _commentary(self, bet: int, mult: float, profit: int) -> str | None:
        client = self._get_groq()
        if not client:
            return None
        try:
            status = "win" if profit > 0 else "loss"
            msg = f"user {status} {abs(profit)} credits - bet {bet} with {mult}x"
            prompt = (
                "you are slug on plinko results. lowercase. minimal emojis. "
                "win: hype. loss small: touch grass. loss 1000+: take break, ncpgambling.org. be creative."
            )
            c = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "system", "content": prompt}, {"role": "user", "content": msg}],
                temperature=0.8,
            )
            return c.choices[0].message.content.lower()
        except Exception as e:
            _log.error("ai error: %s", e)
            return None

    @commands.hybrid_command(name="plinko", description="drop a ball through the plinko board", help="Drop a ball through the plinko board. Choose risk mode: low (0.5x-1.5x), medium (0.2x-3x), or high (0x-5x). Watch the ball bounce down to your multiplier. AI commentary from Slug.")
    async def plinko(self, ctx, amount: int):
        data = load_bank()
        data = open_account(ctx.author.id, data)
        uid = str(ctx.author.id)
        data = await debt_prompt(ctx, self.bot, data, ctx.author.id)

        if amount <= 0:
            return await ctx.send("amount must be greater than zero!")
        if amount > data[uid]["wallet"]:
            return await ctx.send(embed=discord.Embed(description="⊘ insufficient cores", color=0xff4500))

        stats = {
            "plays": data[uid].get("plinko_plays", 0) + 1,
            "biggest_win": data[uid].get("plinko_biggest_win", 0),
            "biggest_loss": data[uid].get("plinko_biggest_loss", 0),
            "net": data[uid].get("plinko_net", 0),
        }

        embed = discord.Embed(
            title="╼ plinko ╾",
            description=f"select risk mode\n\nbet: ⌬ {amount:,}\nwallet: {data[uid]['wallet']:,} cores",
            color=0x2b2d31
        )
        msg = await ctx.send(embed=embed)
        for e in RISK_EMOJIS:
            await msg.add_reaction(e)

        def check(r, u):
            return u == ctx.author and r.message.id == msg.id and str(r.emoji) in RISK_EMOJIS

        try:
            r, _ = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
        except asyncio.TimeoutError:
            return await msg.edit(embed=discord.Embed(description="⌛ timed out selecting risk", color=0xed4245))

        risk = RISK_EMOJIS[str(r.emoji)]
        mode = RISK_MODES[risk]
        multiplier = random.choices(mode["multipliers"], weights=mode["weights"])[0]
        slot_idx = mode["multipliers"].index(multiplier)
        final_col = int(slot_idx * (TOTAL_COLS - 1) / (len(SLOTS) - 1))
        await msg.clear_reactions()

        current_col = TOTAL_COLS // 2
        path = []
        for r in range(ROWS):
            path.append(current_col)
            if r < ROWS - 1:
                if current_col < final_col:
                    current_col += random.choices([1, 0], weights=[75, 25])[0]
                elif current_col > final_col:
                    current_col -= random.choices([1, 0], weights=[75, 25])[0]
                else:
                    current_col += random.choices([-1, 0, 1], weights=[20, 60, 20])[0]
                current_col = max(0, min(TOTAL_COLS - 1, current_col))

        for r in range(ROWS):
            board = build_board(path, path[r], r)
            embed.description = f"```\n{board}\n```"
            embed.set_footer(text=f"{risk} risk · ⌬ {amount:,} bet")
            await msg.edit(embed=embed)
            await asyncio.sleep(0.35)

        winnings = int(amount * multiplier)
        profit = winnings - amount
        apply_loss(uid, data, amount)
        dp, _ = apply_earnings(uid, data, winnings) if winnings > 0 else (0, 0)

        if profit > stats["biggest_win"]:
            stats["biggest_win"] = profit
        if profit < stats["biggest_loss"]:
            stats["biggest_loss"] = profit
        stats["net"] += profit

        data[uid]["plinko_plays"] = stats["plays"]
        data[uid]["plinko_biggest_win"] = stats["biggest_win"]
        data[uid]["plinko_biggest_loss"] = stats["biggest_loss"]
        data[uid]["plinko_net"] = stats["net"]
        save_bank(data)

        ai = self._commentary(amount, multiplier, profit)

        line = f"bet: ⌬ {amount}\nmultiplier: {multiplier}x\n"
        if profit >= 0:
            line += f"winnings: ⌬ {winnings} (+⌬ {profit})"
            color = 0x57f287
        else:
            line += f"loss: ⌬ {abs(profit)}"
            color = 0xed4245
        if dp:
            line += f"\n⌬ {dp:,} to debt"

        embed.color = color
        embed.description = f"```\n{build_board(path, path[-1], ROWS - 1)}\n```\n{line}"
        embed.set_footer(text=f"{risk} risk · wallet: {data[uid]['wallet']:,} cores")
        if ai:
            embed.add_field(name="slug says", value=ai, inline=False)
        await msg.edit(embed=embed)

    @commands.hybrid_command(name="plinkostats", aliases=["pstats"], description="check your plinko stats", help="Shows your plinko plays, biggest win, biggest loss, and net cores.")
    async def plinkostats(self, ctx):
        data = load_bank()
        data = open_account(ctx.author.id, data)
        uid = str(ctx.author.id)
        s = {
            "plays": data[uid].get("plinko_plays", 0),
            "biggest_win": data[uid].get("plinko_biggest_win", 0),
            "biggest_loss": data[uid].get("plinko_biggest_loss", 0),
            "net": data[uid].get("plinko_net", 0),
        }
        if not s["plays"]:
            return await ctx.send(embed=discord.Embed(description="no plinko history yet.", color=0x2b2d31))
        e = discord.Embed(title="plinko stats", color=0x2b2d31)
        e.add_field(name="plays", value=str(s["plays"]), inline=True)
        e.add_field(name="biggest win", value=f"⌬ {s['biggest_win']:,}", inline=True)
        e.add_field(name="biggest loss", value=f"⌬ {s['biggest_loss']:,}", inline=True)
        e.add_field(name="net", value=f"⌬ {s['net']:,}", inline=True)
        await ctx.send(embed=e)

async def setup(bot) -> None:
    await bot.add_cog(Plinko(bot))