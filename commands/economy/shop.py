import discord
from discord.ext import commands
from helpers.storage import load, save
from helpers.economy_base import load_bank, save_bank, open_account
from helpers.admins_config import is_admin
from commands.economy.history import add_tx

SHOP_FILE = "shop.msgpack"
INVENTORY_FILE = "inventory.msgpack"

SHOP_ITEMS = {
    "extra_luck": {"name": "Extra Luck", "description": "+15% success on crime and robbery, +10% better gambling odds. Lady luck smiles on you.", "price": 30000, "role": None},
    "stealthy_shoes": {"name": "Stealthy Shoes", "description": "Move like a shadow. Halve fines when caught, steal 10% more in robberies.", "price": 45000, "role": None},
    "invisibility_potion": {"name": "Invisibility Potion", "description": "Erase your tracks. Crimes leave no trace in logs, +5% success on shady activities.", "price": 60000, "role": None},
}

INV_MAX = 50

def load_shop():
    data = load(SHOP_FILE)
    if not data:
        return dict(SHOP_ITEMS)
    return data

def save_shop(data):
    save(SHOP_FILE, data)

def load_inv():
    return load(INVENTORY_FILE)

def save_inv(data):
    save(INVENTORY_FILE, data)

def user_has_item(user_id: int, item_key: str) -> bool:
    inv = load_inv()
    uid = str(user_id)
    items = inv.get(uid, [])
    return any(i["item"] == item_key for i in items)

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
                description=f"✖ item `{item_name}` not found. use `!shop` to see available items.",
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

        inv = load_inv()
        uid_inv = inv.setdefault(uid, [])
        if len(uid_inv) >= INV_MAX:
            return await ctx.send(embed=discord.Embed(
                description=f"⊘ your inventory is full (max {INV_MAX} items).",
                color=0xff4500
            ))

        data[uid]["wallet"] -= price
        save_bank(data)

        uid_inv.append({"item": k, "name": item["name"], "purchased_at": discord.utils.utcnow().isoformat()})
        save_inv(inv)

        add_tx(ctx.author.id, "purchase", -price, item["name"])
        await ctx.send(embed=discord.Embed(
            description=f"√ purchased **{item['name']}** for **⌬ {price:,}**",
            color=0x57f287
        ))

    @commands.hybrid_command(name="inventory", aliases=["inv"], description="view your purchased items", help="Shows all items you've purchased from the shop. Use !shop to browse available items and !buy <item> to purchase.")
    async def inventory(self, ctx):
        inv = load_inv()
        uid = str(ctx.author.id)
        items = inv.get(uid, [])
        if not items:
            return await ctx.send(embed=discord.Embed(
                description="your inventory is empty. use `!shop` to browse items.",
                color=0x2b2d31
            ))

        embed = discord.Embed(title=f"◈ inventory ({len(items)}/{INV_MAX})", color=0x2b2d31)
        for entry in items:
            embed.add_field(name=entry["name"], value=f"purchased {entry['purchased_at'][:10]}", inline=False)
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
