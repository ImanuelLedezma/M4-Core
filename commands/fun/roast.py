import discord
import random
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType

ROASTS = [
    "if brains were dynamite, you couldn't blow your hat off",
    "you're the human equivalent of a participation trophy",
    "i'd roast you harder but my mom said i'm not allowed to burn trash",
    "you have the charisma of a wet sock",
    "somewhere out there a tree is tirelessly producing oxygen for you, you owe it an apology",
    "you're not stupid, you just have bad luck thinking",
    "your wifi password is probably your only secret",
    "you're like a cloud. when you disappear, it's a beautiful day",
    "if you were a spice, you'd be flour",
    "you have something on your chin. no, the third one",
    "you're the reason the gene pool needs a lifeguard",
    "you bring everyone so much joy... when you leave the room",
    "you're as useless as the 'ueue' in 'queue'",
    "if you were any slower, you'd be going backwards",
    "you're the human version of a typo",
    "you have the perfect face for radio",
    "you're like a software update. whenever i see you, i think 'not now'",
    "if you were a vegetable, you'd be a 'cabbage'",
    "you're the reason they put instructions on shampoo bottles",
    "i've seen salads more intimidating than you",
    "you're like a broken pencil. pointless",
    "if you were any more basic, you'd be a circle",
    "you're the offline button on a website",
    "you have the personality of a default avatar",
    "you're living proof that evolution can go backwards",
    "if you were a startup, you'd be a failed pivot",
]

CLASSIC_ROASTS = [
    "the angels didn't descend for you, you ascended for them",
    "i would agree with you but then we'd both be wrong",
    "you're not a complete waste of space. you're missing a few parts",
    "some day you'll go far. i hope you stay there",
    "i'd explain it to you but i don't have a crayon",
]

class Roast(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="roast", description="burn a member with a savage roast", help="Roast yourself or someone else with a random savage burn. If targeting someone else, uses the classic roast collection.")
    @cooldown(1, 5, BucketType.user)
    async def roast(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        pool = CLASSIC_ROASTS if member and member.id != ctx.author.id else ROASTS
        embed = discord.Embed(
            title=f"🔥 roasting {target.display_name}",
            description=f"*{random.choice(pool)}*",
            color=0xf1c40f
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text=f"requested by {ctx.author.display_name}")
        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Roast(bot))