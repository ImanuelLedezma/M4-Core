import discord
import random
import asyncio
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType

DEVICES = [
    "MacBook Pro 2021", "Dell XPS 15", "ThinkPad X1 Carbon", "Razer Blade 15",
    "HP Spectre x360", "Surface Pro 9", "iPhone 14 Pro", "Samsung Galaxy S23",
    "Google Pixel 7", "iPad Air 5", "Amazon Fire HD 10", "Nintendo Switch",
    "Steam Deck", "Asus ROG Ally", "Framework Laptop 16",
]

OS_LIST = [
    "Windows 11 Home", "Ubuntu 22.04 LTS", "macOS Ventura 13.2",
    "Arch Linux (btw)", "Fedora 38", "Debian 12", "Kali Linux 2023.2",
    "Manjaro 22.0", "Red Hat Enterprise Linux 9", "openSUSE Leap 15.4",
    "elementary OS 7.1", "Zorin OS 16", "ChromeOS", "iOS 17", "Android 14",
]

STREETS = [
    "Oak Street", "Maple Avenue", "Pine Road", "Cedar Lane", "Elm Boulevard",
    "Birch Court", "Spruce Drive", "Willow Way", "Ash Terrace", "Cherry Circle",
    "Poplar Street", "Hawthorn Avenue", "Juniper Lane", "Magnolia Drive",
]

CITIES = [
    "Springfield", "Shelbyville", "Ogdenville", "North Haverbrook", "Brockway",
    "Capital City", "Cypress Creek", "Waverly Hills", "Little Pwagmattasquarmsettport",
    "New Bedlam", "Sprooklyn", "Seinfeld", "Quahog", "Langley Falls",
]

PASSWORDS = [
    "hunter2", "password123", "iloveyou", "qwerty", "letmein", "abc123",
    "monkey", "dragon", "sunshine", "football", "princess", "welcome",
    "admin", "login", "passw0rd", "starwars", "12345678", "master",
    "hello", "freedom", "trustno1", "shadow", "superman", "batman",
]

BANKS = [
    "First National Bank", "Shelbyville Credit Union", "Springfield Savings",
    "Ogden Federal", "North Haverbrook Bank", "Brockway Trust",
    "Capital City Bank", "Cypress Creek Credit Union", "Waverly Hills Savings",
    "Little Pwagmattasquarmsettport Bank", "New Bedlam Federal",
    "Sprooklyn National", "Seinfeld State Bank", "Quahog Savings & Loan",
]

EXPLOITS = [
    "CVE-2024-0001", "CVE-2024-1337", "CVE-2023-5000", "ZDI-24-001",
    "MS08-067 (classic)", "EternalBlue", "ZeroLogon", "PrintNightmare",
    "Log4Shell (still trying)", "Dirty Pipe",
]

def fake_ip():
    return f"{random.randint(100,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

def fake_mac():
    return ":".join(f"{random.randint(0,255):02x}" for _ in range(6))

class Hack(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="hack", description="simulate hacking a user", help="Simulate hacking a user with a 10-step animated sequence. Shows fake IP, MAC, device, OS, location, passwords, bank details, and exploit. All fictional.")
    @cooldown(1, 10, BucketType.user)
    async def hack(self, ctx, member: discord.Member):
        ip = fake_ip()
        mac = fake_mac()
        device = random.choice(DEVICES)
        os_name = random.choice(OS_LIST)
        street = f"{random.randint(1,9999)} {random.choice(STREETS)}"
        city = random.choice(CITIES)
        state = random.choice(["TX", "CA", "NY", "FL", "OH", "WA", "IL", "PA", "MI", "GA"])
        zipcode = random.randint(10000, 99999)
        bank = random.choice(BANKS)
        balance = round(random.uniform(0.50, 99.99), 2)
        passwords = random.sample(PASSWORDS, 4)
        exploit = random.choice(EXPLOITS)

        steps = [
            (f"⟳ scanning open ports on {member.mention}...", False),
            (f"⟳ resolving ip address... `{ip}`", False),
            (f"⟳ fingerprinting device... `{device}` running `{os_name}`", False),
            (f"⟳ exploiting `{exploit}`...", False),
            (f"⟳ spoofing mac address... `{mac}`", False),
            (f"⟳ triangulating location... `{street}, {city}, {state} {zipcode}`", False),
            ("⟳ breaching password vault...", False),
            (f"⟳ cracking {len(passwords)} password hashes...", False),
            (f"⟳ accessing bank records... `{bank}`", False),
            ("√ hack complete!", True),
        ]

        embed = discord.Embed(title="⟳ hacking...", description=steps[0][0], color=discord.Color.red())
        msg = await ctx.send(embed=embed)

        for desc, _ in steps[1:]:
            await asyncio.sleep(1.0)
            embed.description = desc
            await msg.edit(embed=embed)

        await asyncio.sleep(0.8)

        result_embed = discord.Embed(
            title=f"√ hacked {member.display_name}",
            color=discord.Color.red()
        )
        result_embed.set_thumbnail(url=member.display_avatar.url)
        result_embed.add_field(name="ip address", value=f"`{ip}`", inline=True)
        result_embed.add_field(name="mac address", value=f"`{mac}`", inline=True)
        result_embed.add_field(name="device", value=f"`{device}`", inline=True)
        result_embed.add_field(name="os", value=f"`{os_name}`", inline=True)
        result_embed.add_field(name="location", value=f"`{street}, {city}, {state} {zipcode}`", inline=False)
        result_embed.add_field(name="bank", value=f"`{bank}` · `${balance}`", inline=False)
        result_embed.add_field(name="passwords found", value="\n".join(f"`{p}`" for p in passwords), inline=False)
        result_embed.add_field(name="exploit used", value=f"`{exploit}`", inline=True)
        await msg.edit(embed=result_embed)

    @hack.error
    async def hack_error(self, ctx, error):
        error.handled = True
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(
                title="✖ missing target",
                description="usage: `!hack @member`",
                color=discord.Color.red()
            ))

async def setup(bot) -> None:
    await bot.add_cog(Hack(bot))