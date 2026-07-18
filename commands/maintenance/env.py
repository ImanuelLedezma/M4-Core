import asyncio
import discord
import os
from discord.ext import commands
from helpers.admins_config import is_admin

ENV_FILE = ".env"

def read_env() -> dict:
    env = {}
    if not os.path.exists(ENV_FILE):
        return env
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env

def write_env(env: dict):
    with open(ENV_FILE, "w") as f:
        for k, v in env.items():
            f.write(f"{k}={v}\n")

def mask(value: str) -> str:
    if len(value) <= 6:
        return "***"
    return value[:3] + "***" + value[-3:]

class Env(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="env", aliases=["environment"], description="manage environment variables", help="Read or modify environment variables. Usage: !env (list all), !env KEY (get value), !env KEY VALUE (set value). All actions require confirmation via reaction. Admin only.")
    async def env_cmd(self, ctx, name: str = None, *, value: str = None):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized.", color=0xff4500))

        if name is None:
            action_desc = "read the contents of all environment variables"
            action = "read_all"
        elif value is None:
            action_desc = f"read the contents of `{name}`"
            action = "read_one"
        else:
            action_desc = f"change the value of `{name}`"
            action = "write"

        warn_embed = discord.Embed(
            title="⚠ wait! are you sure?",
            description=(
                f"this will **{action_desc}** and make them visible to {ctx.channel.mention}!"
            ),
            color=0xff4500
        )
        warn_msg = await ctx.send(embed=warn_embed)
        await warn_msg.add_reaction("✅")
        await warn_msg.add_reaction("❌")

        def check(reaction, user):
            return (
                user.id == ctx.author.id
                and reaction.message.id == warn_msg.id
                and str(reaction.emoji) in ("✅", "❌")
            )

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await warn_msg.edit(embed=discord.Embed(description="⊘ timed out.", color=0xff4500))
            try: await warn_msg.clear_reactions()
            except discord.Forbidden: pass
            return

        try: await warn_msg.clear_reactions()
        except discord.Forbidden: pass

        if str(reaction.emoji) == "❌":
            return await warn_msg.edit(embed=discord.Embed(description="✖ cancelled.", color=0xff4500))

        env = read_env()

        if action == "write":
            env[name] = value
            write_env(env)
            os.environ[name] = value
            await warn_msg.edit(embed=discord.Embed(
                description=f"√ `{name}` set to `{mask(value)}`.",
                color=0x57f287
            ))

        elif action == "read_one":
            val = env.get(name) or os.getenv(name)
            if val is None:
                await warn_msg.edit(embed=discord.Embed(
                    description=f"✖ `{name}` not found in `.env`.",
                    color=0xff4500
                ))
            else:
                embed = discord.Embed(color=0x2b2d31)
                embed.add_field(name=f"◈ {name}", value=f"`{val}`", inline=False)
                await warn_msg.edit(embed=embed)

        elif action == "read_all":
            if not env:
                await warn_msg.edit(embed=discord.Embed(
                    description="✖ `.env` is empty or not found.",
                    color=0xff4500
                ))
            else:
                lines = "\n".join(f"{k}={v}" for k, v in env.items())
                if len(lines) > 1900:
                    lines = lines[:1900] + "\n..."
                embed = discord.Embed(
                    title="◈ .env contents",
                    description=f"```\n{lines}\n```",
                    color=0x2b2d31
                )
                await warn_msg.edit(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Env(bot))