import discord
import random
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType
from datetime import datetime, timedelta

CAUSES = [
    "tripped over a single grape",
    "fell into a black hole",
    "was hit by a bus",
    "aggressively yeeted off a chair by a pigeon",
    "book fell on head at terminal velocity",
    "consumed 47 energy drinks in one sitting",
    "argued with a vending machine and lost",
    "sat on a lego at exactly the wrong angle",
    "attacked by a very opinionated goose",
    "was struck by lightning while using a umbrella",
    "spontaneously combusted during a yawn",
    "choked on the concept of a monday",
    "had a fatal allergic reaction to sunlight",
    "was outsmarted by a particularly cunning door",
    "brained by a rogue frisbee thrown in 1987",
    "disagreed with gravity one too many times",
    "opened too many chrome tabs simultaneously",
    "challenged a raccoon to a staring contest",
    "hit by a forgotten shopping cart in a parking lot",
    "made eye contact with the microwave for too long",
    "fell into a void while looking for their keys",
    "stepped on wet floor sign instead of avoiding it",
    "overloaded brain by reading terms and conditions",
    "attempted to pet a wild squirrel and failed",
    "got into a heated debate with a stop sign and lost",
    "defeated in battle by a particularly aggressive houseplant",
    "slain by a rogue autocorrect suggestion",
    "crushed by an avalanche of unwashed laundry",
    "was overwhelmed by the sheer number of streaming services available",
    "was fatally distracted by a butterfly and wandered into traffic",
    "perished while trying to fold a fitted sheet",
    "died of embarrassment after a typo in a work email",
    "was taken out by a stray shopping cart",
    "expired while waiting for a loading screen",
    "vanished while looking for their other sock",
]

LAST_WORDS = [
    '"oh no!"', '"i wasnt ready for this."', '"wait, what?"',
    '"i probably shouldve seen this coming."', '"hold on let me google this."',
    '"thats fine."', '"can we reschedule?"', '"technically im fine."',
    '"no wait—"', '"i have a bad feeling about this."', '"uh, this is awkward."',
    '"im not sure how to feel about this."', '"well, this is unexpected."',
    '"it was worth it."', '"at least i had snacks."', '"ill be fine. probably."',
    '"bruh."', '"worth it."', '"so... no head?"',
]

class DeathDate(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="deathdate", aliases=["death", "rip"], description="predict when someone will die", help="Generate a fictional death certificate with date, age, cause of death, last words, and zodiac sign. All fictional. Probably.")
    @cooldown(1, 5, BucketType.user)
    async def deathdate(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        now = datetime.now()

        days = random.randint(1, 365 * 60)
        future = now + timedelta(days=days)
        date_str = future.strftime("%B %d, %Y")
        age = future.year - target.created_at.year
        cause = random.choice(CAUSES)
        last = random.choice(LAST_WORDS)

        zodiac = ["aries", "taurus", "gemini", "cancer", "leo", "virgo",
                   "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"][future.month - 1]

        embed = discord.Embed(
            title=f"☠ death certificate · {target.display_name}",
            color=0x2b2d31
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="date of passing", value=f"`{date_str}`", inline=True)
        embed.add_field(name="age at passing", value=f"`{age}`", inline=True)
        embed.add_field(name="zodiac sign", value=f"`{zodiac}`", inline=True)
        embed.add_field(name="cause of death", value=cause, inline=False)
        embed.add_field(name="last words", value=last, inline=False)
        embed.set_footer(text="fictional. probably.")
        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(DeathDate(bot))