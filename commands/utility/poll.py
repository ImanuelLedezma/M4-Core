import discord
from discord.ext import commands

YES_NO_EMOJIS = ["👍", "👎"]
MULTIPLE_CHOICE_EMOJIS = ["🇦", "🇧", "🇨", "🇩", "🇪", "🇫", "🇬", "🇭"]

class Poll(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="poll", aliases=["vote", "question"], description="create a yes/no or multiple choice poll", help="Create a poll. Simple yes/no: !poll Is water wet? Multiple choice: !poll What's for dinner?\nPizza\nTacos\nSushi (up to 8 options, one per line)")
    async def poll(self, ctx, *, question_or_options: str):
        lines = question_or_options.strip().split("\n")
        question = lines[0]
        options = [l.strip().strip("-*") for l in lines[1:] if l.strip()]

        if not options:
            embed = discord.Embed(
                title="📊 poll",
                description=question,
                color=0x2b2d31
            )
            embed.set_footer(text=f"by {ctx.author.display_name} · react to vote")
            msg = await ctx.send(embed=embed)
            for e in YES_NO_EMOJIS:
                await msg.add_reaction(e)
            return

        if len(options) > 8:
            return await ctx.send(embed=discord.Embed(
                description="⊘ max 8 options allowed.",
                color=0xff4500
            ))

        embed = discord.Embed(
            title=f"📊 {question}",
            color=0x2b2d31
        )
        desc = []
        for i, opt in enumerate(options):
            desc.append(f"{MULTIPLE_CHOICE_EMOJIS[i]} {opt[:200]}")
        embed.description = "\n".join(desc)
        embed.set_footer(text=f"by {ctx.author.display_name} · react to vote")
        msg = await ctx.send(embed=embed)

        for i in range(len(options)):
            await msg.add_reaction(MULTIPLE_CHOICE_EMOJIS[i])

async def setup(bot) -> None:
    await bot.add_cog(Poll(bot))