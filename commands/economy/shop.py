import discord
import random
from discord.ext import commands
from helpers.economy_base import load_bank, save_bank, open_account
from helpers.admins_config import is_admin
from commands.economy.history import add_tx
from helpers.database import shop_list, shop_save, inv_get, inv_add, inv_remove, inv_count, inv_user_has

SHOP_ITEMS = {
    "donut": {"name": "Donut", "description": "Bribe the fuzz with a glazed donut. Halves your next fine when busted on crime or robbery.", "price": 5000, "role": None},
    "pet_rock": {"name": "Pet Rock", "description": "A very good rock. It stares back. Does absolutely nothing. Collectible.", "price": 500, "role": None},
    "lucky_socks": {"name": "Lucky Socks", "description": "Never wash 'em. +5% win rate on all gambling. Your coinflip and blackjack results improve slightly.", "price": 6000, "role": None},
    "fake_license": {"name": "Fake License", "description": "Look legitimate. Reduces crime and robbery cooldown by 1 minute each.", "price": 8000, "role": None},
    "mystery_box": {"name": "Mystery Box", "description": "Who knows what's inside? Buy one and use !open to reveal a random prize — or a total loss.", "price": 15000, "role": None},
    "alarm_system": {"name": "Alarm System", "description": "Protect your wallet with motion sensors and lasers. When someone robs you, 30% chance they get caught and pay double.", "price": 25000, "role": None},
    "extra_luck": {"name": "Extra Luck", "description": "+15% success on crime and robbery, +10% better gambling odds. Lady luck smiles on you.", "price": 30000, "role": None},
    "stealthy_shoes": {"name": "Stealthy Shoes", "description": "Move like a shadow. Steal 15% more in robberies, and victims are notified a full minute later.", "price": 45000, "role": None},
    "invisibility_potion": {"name": "Invisibility Potion", "description": "Erase your tracks. Crimes leave no trace in logs, +5% success on shady activities.", "price": 60000, "role": None},
}

INV_MAX = 50


def load_shop():
    data = shop_list()
    if not data:
        shop_save(SHOP_ITEMS)
        return dict(SHOP_ITEMS)
    return {r["key"]: {"name": r["name"], "description": r["description"], "price": r["price"], "role": r["role_id"]} for r in data}


def save_shop(items):
    shop_save(items)


def user_has_item(user_id: int, item_key: str) -> bool:
    return inv_user_has(user_id, item_key)


class Shop(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="shop", description="list items available for purchase", help="Browse the shop and see what items are available to buy with cores. Shows item name, price, and description.")
    async def shop(self, ctx):
        items = load_shop()
        if not items:
            return await ctx.send(embed=discord.Embed(description="shop is empty.", color=0x2b2d31))

        embed = discord.Embed(title="◈ shop", color=0x2b2d31)
        for key, item in items.items():
            embed.add_field(
                name=f"**{item['name']}** · ⌬ {item['price']:,}",
                value=item["description"][:100],
                inline=False,
            )
        embed.set_footer(text="use !buy <item> to purchase")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="buy", description="purchase an item from the shop", help="Buy an item from the shop using cores from your wallet. Item is added to your inventory. Use !shop to see available items. Example: !buy vip")
    async def buy(self, ctx, *, item_name: str):
        items = load_shop()
        key = item_name.strip().lower()

        found = None
        for k, v in items.items():
            if k == key or v["name"].lower() == key:
                found = (k, v)
                break
        if not found:
            return await ctx.send(embed=discord.Embed(
                description=f"⊘ item `{item_name}` not found. use `!shop` to see available items.",
                color=0xff4500
            ))

        k, item = found
        price = item["price"]

        data = load_bank()
        data = open_account(ctx.author.id, data)
        uid = str(ctx.author.id)

        if data[uid]["wallet"] < price:
            return await ctx.send(embed=discord.Embed(
                description=f"⊘ you need **⌬ {price:,}** to buy **{item['name']}**. you have **⌬ {data[uid]['wallet']:,}** in your wallet.",
                color=0xff4500
            ))

        if inv_count(ctx.author.id) >= INV_MAX:
            return await ctx.send(embed=discord.Embed(
                description=f"⊘ your inventory is full (max {INV_MAX} items).",
                color=0xff4500
            ))

        data[uid]["wallet"] -= price
        save_bank(data)

        inv_add(ctx.author.id, k, item["name"])

        add_tx(ctx.author.id, "purchase", -price, item["name"])
        await ctx.send(embed=discord.Embed(
            description=f"√ purchased **{item['name']}** for **⌬ {price:,}**",
            color=0x57f287
        ))

    @commands.hybrid_command(name="inventory", aliases=["inv"], description="view your purchased items", help="Shows all items you've purchased from the shop. Use !shop to browse available items and !buy <item> to purchase.")
    async def inventory(self, ctx):
        items = inv_get(ctx.author.id)
        if not items:
            return await ctx.send(embed=discord.Embed(
                description="your inventory is empty. use `!shop` to browse items.",
                color=0x2b2d31
            ))

        embed = discord.Embed(title=f"◈ inventory ({len(items)}/{INV_MAX})", color=0x2b2d31)
        for entry in items:
            name = entry["name"]
            if entry["item"] == "mystery_box":
                name += " · use !open to reveal"
            embed.add_field(name=name, value=f"purchased {entry['purchased_at'][:10]}", inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="open", description="open a mystery box from your inventory", help="Open a Mystery Box to reveal a random prize. You might win cores, items, or walk away with nothing. Each box is consumed on use.")
    async def open_box(self, ctx):
        if not inv_remove(ctx.author.id, "mystery_box"):
            return await ctx.send(embed=discord.Embed(
                description="⊘ you don't have any mystery boxes. buy one with `!buy mystery box`.",
                color=0xff4500
            ))

        uid = str(ctx.author.id)
        roll = random.random()
        if roll < 0.05:
            prize = random.randint(50000, 100000)
            desc = f"╼ **JACKPOT!** ╾\nthe box explodes with confetti. **⌬ {prize:,}** cores spill out!"
            color = 0xffd700
        elif roll < 0.2:
            prize = random.randint(5000, 25000)
            desc = f"╼ **lucky box** ╾\nyou found **⌬ {prize:,}** cores inside!"
            color = 0x57f287
        elif roll < 0.5:
            prize = random.randint(500, 4000)
            desc = f"╼ not bad ╾\nthere's **⌬ {prize:,}** cores in here."
            color = 0x2b2d31
        elif roll < 0.8:
            prize = 0
            items_list = ["a single sock", "an expired coupon", "a broken pencil", "sand", "lint", "a used napkin"]
            desc = f"╼ **trash** ╾\nit's just {random.choice(items_list)}. nothing valuable."
            color = 0xff4500
        else:
            prize = -random.randint(1000, 5000)
            desc = f"⊘ **it's a trap!**\na spring-loaded boxing glove hits you in the face. you lose **⌬ {abs(prize):,}** cores."
            color = 0xff4500

        if prize > 0:
            data = load_bank()
            data = open_account(ctx.author.id, data)
            data[uid]["wallet"] += prize
            save_bank(data)
            add_tx(ctx.author.id, "earn", prize, "mystery box")
        elif prize < 0:
            data = load_bank()
            data = open_account(ctx.author.id, data)
            data[uid]["wallet"] = max(0, data[uid]["wallet"] + prize)
            save_bank(data)
            add_tx(ctx.author.id, "loss", prize, "mystery box trap")

        embed = discord.Embed(title="◈ mystery box", description=desc, color=color)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="shopadd", description="add an item to the shop (admin)", help="Add a new item to the shop. Usage: !shopadd <key> <name> <price> <description>. Admin only.")
    async def shopadd(self, ctx, key: str, name: str, price: int, *, description: str):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized.", color=0xff4500))
        items = load_shop()
        items[key.lower()] = {"name": name, "description": description, "price": price, "role": None}
        save_shop(items)
        await ctx.send(embed=discord.Embed(description=f"√ added **{name}** (⌬ {price:,}) to the shop", color=0x57f287))

    @commands.hybrid_command(name="shopremove", description="remove an item from the shop (admin)", help="Remove an item from the shop by key. Usage: !shopremove <key>. Admin only.")
    async def shopremove(self, ctx, key: str):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized.", color=0xff4500))
        items = load_shop()
        key = key.lower()
        if key not in items:
            return await ctx.send(embed=discord.Embed(description=f"⊘ item `{key}` not found.", color=0xff4500))
        name = items[key]["name"]
        del items[key]
        save_shop(items)
        await ctx.send(embed=discord.Embed(description=f"√ removed **{name}** from the shop", color=0x57f287))

async def setup(bot) -> None:
    await bot.add_cog(Shop(bot))
