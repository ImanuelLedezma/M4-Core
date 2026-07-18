import discord
import random
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType

DILEMMAS = [
    ("never use the internet again", "never watch TV or movies again"),
    ("be able to fly", "be invisible"),
    ("always be 10 minutes late", "always be 20 minutes early"),
    ("have unlimited money but no friends", "have unlimited friends but no money"),
    ("know how you'll die", "know when you'll die"),
    ("be famous but hated", "be unknown but loved"),
    ("eat only sweet food forever", "eat only savory food forever"),
    ("be able to speak every language", "be able to play every instrument"),
    ("live in extreme heat", "live in extreme cold"),
    ("have no phone for a year", "have no music for a year"),
    ("always tell the truth", "always lie"),
    ("be able to read minds", "be able to see the future"),
    ("never sleep again", "never dream again"),
    ("fight 100 duck-sized horses", "fight 1 horse-sized duck"),
    ("have fingers as toes", "have toes as fingers"),
    ("only whisper forever", "only shout forever"),
    ("lose all your memories from birth to 18", "lose all your memories from the last 5 years"),
    ("always itch but never scratch", "always feel like sneezing but never sneeze"),
    ("be able to teleport", "be able to time travel"),
    ("never be able to use social media", "never be able to watch youtube"),
    ("only be able to eat food that's been blended into a smoothie", "only be able to eat food that's been deep fried"),
    ("have a rewind button for your life", "have a pause button for your life"),
    ("be able to control animals with your mind", "be able to control electronics with your mind"),
    ("always have to say everything on your mind", "never speak again"),
    ("have a personal chef but no fridge", "have a fridge but no food in it"),
    ("be able to breathe underwater", "be able to survive in space"),
    ("have a photographic memory but be terrible at math", "be a math genius but have a terrible memory"),
    ("only be able to communicate through song lyrics", "only be able to communicate through movie quotes"),
    ("have a pet dinosaur but it's the size of a cat", "have a pet cat but it's the size of a dinosaur"),
    ("always know when someone is lying", "always win at any game"),
    ("be able to speak to animals", "be able to speak every human language"),
    ("be invisible but only when no one is looking", "be able to fly but only 2 feet off the ground"),
    ("have unlimited pizza for life", "have unlimited sushi for life"),
    ("live in a treehouse", "live in a submarine"),
    ("be the funniest person in the room", "be the smartest person in the room"),
]

class WouldYouRather(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="wyr", aliases=["wouldyourather"], description="get a random would you rather question", help="Get a random would-you-rather dilemma with reaction voting so the server can vote on the options.")
    @cooldown(1, 5, BucketType.user)
    async def wyr(self, ctx):
        a, b = random.choice(DILEMMAS)
        embed = discord.Embed(
            title="◈ would you rather...",
            color=0x5865f2
        )
        embed.add_field(name="🅐", value=a, inline=True)
        embed.add_field(name="🅑", value=b, inline=True)
        embed.set_footer(text="react with 🅐 or 🅑 to vote")
        msg = await ctx.send(embed=embed)
        try:
            await msg.add_reaction("🅐")
            await msg.add_reaction("🅑")
        except (discord.Forbidden, discord.NotFound):
            pass

async def setup(bot) -> None:
    await bot.add_cog(WouldYouRather(bot))