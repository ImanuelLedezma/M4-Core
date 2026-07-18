import discord
from discord.ext import commands
import asyncio
import os
from helpers.admins_config import is_admin

class Pull(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def reload_all_extensions(self):
        results = []
        for root, _, files in os.walk("./commands"):
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    rel_path = os.path.relpath(os.path.join(root, file), ".")
                    module_path = rel_path.replace(os.sep, ".").removesuffix(".py")

                    try:
                        await self.bot.reload_extension(module_path)
                        results.append(f"√ `{module_path}`")
                    except commands.ExtensionNotLoaded:
                        try:
                            await self.bot.load_extension(module_path)
                            results.append(f"√ `{module_path}` (new)")
                        except Exception as e:
                            results.append(f"⊘ `{module_path}`: {e}")
                    except Exception as e:
                        results.append(f"⊘ `{module_path}`: {e}")
        return results

    @commands.hybrid_command(name="pull", description="git pull and reload all cogs", help="Git pull from GitHub and reload all cogs. Usage: !pull (from main), !pull canary. Admin only.")
    async def pull(self, ctx, branch: str = "main"):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized.", color=0xff4500))
        branch = branch.lower()
        if branch not in ["canary", "main"]:
            return await ctx.send("⊘ use `!pull canary` or `!pull main`.")
        status_msg = await ctx.send(embed=discord.Embed(
            title="⟳ pulling",
            description=f"pulling and updating bot internals from **{branch}**...",
            color=0x5865f2
        ))
        try:
            process = await asyncio.create_subprocess_shell(
                f"git fetch origin && git reset --hard origin/{branch}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                raise Exception(stderr.decode())
            reload_logs = await self.reload_all_extensions()
            git_log = stdout.decode().strip()
            if len(git_log) > 500:
                git_log = "..." + git_log[-497:]
            if not git_log:
                git_log = "already up to date."
            log_chunk = "\n".join(reload_logs)
            if len(log_chunk) > 1024:
                log_chunk = log_chunk[:1020] + "..."
            embed = discord.Embed(
                title="√ pulled!",
                description=f"pulled and updated bot internals from `{branch}`.",
                color=0x57f287
            )
            embed.add_field(name="git output", value=f"```\n{git_log}\n```", inline=False)
            embed.add_field(name="bot logs", value=log_chunk or "no cogs found.", inline=False)
            await status_msg.edit(embed=embed)
        except Exception as e:
            err = str(e)
            if len(err) > 1000:
                err = err[:1000] + "..."
            embed = discord.Embed(
                title="⊘ pull failed",
                description=f"```\n{err}\n```",
                color=0xff4500
            )
            embed.add_field(
                name="common causes",
                value="• invalid branch name\n• git not in venv path\n• network issue",
                inline=False
            )
            await status_msg.edit(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Pull(bot))
