import discord
import random
import asyncio
import os
from discord.ext import commands
from groq import Groq
from helpers.economy_base import load_bank, save_bank, open_account, apply_loss, apply_earnings, debt_prompt
from helpers.logging import init as init_logging

_log = init_logging("blackjack")

class Blackjack(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self._groq = None

    def _get_groq(self) -> Groq | None:
        if self._groq is None:
            api_key = os.getenv("GROQ_KEY")
            if api_key:
                self._groq = Groq(api_key=api_key)
        return self._groq

    def _commentary(self, bet: int, result: str, amount: int) -> str | None:
        client = self._get_groq()
        if not client:
            return None
        try:
            prompt = (
                "you are slug, commenting on blackjack results. lowercase only. minimal emojis. "
                "if they win: hype man. if they lose small: touch grass. "
                "if they lose 2000+: take a break, link ncpgambling.org. be creative."
            )
            msg = f"user had a {result} of {amount} credits. bet was {bet}."
            c = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "system", "content": prompt}, {"role": "user", "content": msg}],
                temperature=0.8,
            )
            return c.choices[0].message.content.lower()
        except Exception as e:
            _log.error("ai error: %s", e)
            return None

    _SUITS = ["♠", "♥", "♦", "♣"]
    _FACE = {10: "10", 11: "A"}

    def _deal(self):
        return random.randint(2, 11)

    def _card_str(self, value: int) -> str:
        suit = random.choice(self._SUITS)
        label = self._FACE.get(value, str(value))
        return f"`{label}{suit}`"

    def _hand_value(self, hand: list[int]) -> int:
        total = sum(hand)
        aces = hand.count(11)
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    def _hand_str(self, hand: list[int]) -> str:
        return " ".join(self._card_str(c) for c in hand)

    @commands.hybrid_command(name="blackjack", aliases=["bj"], description="play blackjack against the house", help="Play blackjack with the dealer. Hit (+) or stand (stop). Try to get closer to 21 than the dealer without going over. Blackjack commentary from Slug (AI). Tracks your wins/losses/net. Use !bjstats to see your record.")
    async def blackjack(self, ctx, amount: int):
        data = load_bank()
        data = open_account(ctx.author.id, data)
        uid = str(ctx.author.id)
        data = await debt_prompt(ctx, self.bot, data, ctx.author.id)

        if amount <= 0 or amount > data[uid]["wallet"]:
            return await ctx.send(embed=discord.Embed(description="⊘ insufficient cores in wallet", color=0xff4500))

        player = [self._deal(), self._deal()]
        dealer = [self._deal(), self._deal()]
        uid = str(ctx.author.id)
        stats = {
            "wins": data[uid].get("bj_wins", 0),
            "losses": data[uid].get("bj_losses", 0),
            "pushes": data[uid].get("bj_pushes", 0),
            "net": data[uid].get("bj_net", 0),
        }

        def embed_str(show_dealer=False):
            p = self._hand_value(player)
            d = f"{dealer[0]} + ?"
            if show_dealer:
                d = self._hand_str(dealer)
            e = discord.Embed(title="╼ blackjack ╾", color=0x2b2d31)
            e.add_field(name="◈ your hand", value=f"cards: `{self._hand_str(player)}`\ntotal: `{p}`", inline=True)
            e.add_field(name="◈ dealer", value=f"cards: `{d}`", inline=True)
            p_str = f"wallet: {data[uid]['wallet']:,} cores · bet: ⌬ {amount:,}"
            w = stats["wins"]; l = stats["losses"]; t = stats["pushes"]
            p_str += f"\nrecord: {w}w/{l}l/{t}t"
            if not show_dealer:
                e.set_footer(text=f"{p_str} · ➕ hit | 🛑 stand")
            else:
                e.set_footer(text=p_str)
            return e

        msg = await ctx.send(embed=embed_str())
        await msg.add_reaction("➕")
        await msg.add_reaction("🛑")

        def check(r, u):
            return u == ctx.author and str(r.emoji) in ["➕", "🛑"] and r.message.id == msg.id

        is_blackjack = len(player) == 2 and 11 in player and 10 in player and self._hand_value(player) == 21

        if is_blackjack:
            payout = int(amount * 1.5)
            dp, _ = apply_earnings(uid, data, payout)
            result = f"◈ **blackjack!** +⌬ {payout} (3:2 payout)"
            color = 0x57f287
            stats["wins"] += 1
            stats["net"] += payout
            res_type, res_val = "win", payout
            if dp: result += f"\n⌬ {dp:,} to debt"
            e = embed_str(show_dealer=True)
            e.description = result
            e.color = color
            data[uid]["bj_wins"] = stats["wins"]
            data[uid]["bj_losses"] = stats["losses"]
            data[uid]["bj_pushes"] = stats["pushes"]
            data[uid]["bj_net"] = stats["net"]
            save_bank(data)
            ai = self._commentary(amount, res_type, res_val)
            if ai:
                e.add_field(name="slug says", value=ai, inline=False)
            await msg.edit(embed=e)
            try: await msg.clear_reactions()
            except (discord.Forbidden, discord.NotFound): pass
            return

        while self._hand_value(player) < 21:
            try:
                r, _ = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
                if str(r.emoji) == "➕":
                    player.append(self._deal())
                    await msg.edit(embed=embed_str())
                    try:
                        await msg.remove_reaction(r, _)
                    except (discord.Forbidden, discord.NotFound):
                        pass
                    if self._hand_value(player) >= 21:
                        break
                else:
                    break
            except asyncio.TimeoutError:
                break

        p_total = self._hand_value(player)
        if p_total <= 21:
            while self._hand_value(dealer) < 17:
                dealer.append(self._deal())
        d_total = self._hand_value(dealer)

        if p_total > 21:
            apply_loss(uid, data, amount)
            result = f"⊘ bust.. you lost **⌬ {amount}**"
            color = 0xed4245
            stats["losses"] += 1
            stats["net"] -= amount
            debt = data[uid]["debt"]
            if debt: result += f"\n⌬ {debt:,} in debt"
            res_type, res_val = "loss", amount
        elif d_total > 21:
            dp, _ = apply_earnings(uid, data, amount)
            result = f"◈ dealer bust! +⌬ {amount}"
            color = 0x57f287
            stats["wins"] += 1
            stats["net"] += amount
            res_type, res_val = "win", amount
            if dp: result += f"\n⌬ {dp:,} to debt"
        elif p_total > d_total:
            dp, _ = apply_earnings(uid, data, amount)
            result = f"◈ winner! +⌬ {amount}"
            color = 0x57f287
            stats["wins"] += 1
            stats["net"] += amount
            res_type, res_val = "win", amount
            if dp: result += f"\n⌬ {dp:,} to debt"
        elif p_total < d_total:
            apply_loss(uid, data, amount)
            result = f"⊘ dealer wins.. -⌬ {amount}"
            color = 0xed4245
            stats["losses"] += 1
            stats["net"] -= amount
            debt = data[uid]["debt"]
            if debt: result += f"\n⌬ {debt:,} in debt"
            res_type, res_val = "loss", amount
        else:
            result = "◈ push · cores returned"
            color = 0xfee75c
            stats["pushes"] += 1
            res_type, res_val = "push", 0

        data[uid]["bj_wins"] = stats["wins"]
        data[uid]["bj_losses"] = stats["losses"]
        data[uid]["bj_pushes"] = stats["pushes"]
        data[uid]["bj_net"] = stats["net"]
        save_bank(data)

        ai = self._commentary(amount, res_type, res_val)
        e = embed_str(show_dealer=True)
        e.description = result
        e.color = color
        if ai:
            e.add_field(name="slug says", value=ai, inline=False)
        await msg.edit(embed=e)
        try: await msg.clear_reactions()
        except (discord.Forbidden, discord.NotFound): pass

    @commands.hybrid_command(name="bjstats", aliases=["blackjackstats"], description="check your blackjack stats", help="Shows your blackjack wins, losses, pushes, winrate, net cores, and total games played.")
    async def bjstats(self, ctx):
        data = load_bank()
        data = open_account(ctx.author.id, data)
        uid = str(ctx.author.id)
        s = {
            "wins": data[uid].get("bj_wins", 0),
            "losses": data[uid].get("bj_losses", 0),
            "pushes": data[uid].get("bj_pushes", 0),
            "net": data[uid].get("bj_net", 0),
        }
        total = s["wins"] + s["losses"] + s["pushes"]
        if not total:
            return await ctx.send(embed=discord.Embed(description="no blackjack history yet.", color=0x2b2d31))
        wr = round(s["wins"] / (s["wins"] + s["losses"]) * 100, 1) if s["wins"] + s["losses"] else 0
        e = discord.Embed(title="blackjack stats", color=0x2b2d31)
        e.add_field(name="wins", value=str(s["wins"]), inline=True)
        e.add_field(name="losses", value=str(s["losses"]), inline=True)
        e.add_field(name="pushes", value=str(s["pushes"]), inline=True)
        e.add_field(name="winrate", value=f"{wr}%", inline=True)
        e.add_field(name="net", value=f"⌬ {s['net']:,}", inline=True)
        e.add_field(name="games", value=str(total), inline=True)
        await ctx.send(embed=e)

async def setup(bot) -> None:
    await bot.add_cog(Blackjack(bot))