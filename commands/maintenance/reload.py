import discord
from discord.ext import commands
import os
from helpers.admins_config import is_admin

class Admin(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="reload", description="reload all cogs or a specific one", help="Reload all cogs or a specific extension. Usage: !reload (all), !reload commands.economy.bal (specific). Admin only.")
    async def reload(self, ctx, cog: str = None):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized.", color=0xff4500))

        status_msg = await ctx.send(embed=discord.Embed(
            title="⟳ reloading",
            description="reloading extensions...",
            color=0x2b2d31
        ))

        if cog:
            try:
                await self.bot.reload_extension(cog)
                await status_msg.edit(embed=discord.Embed(
                    title="√ reloaded",
                    description=f"reloaded `{cog}`",
                    color=0x57f287
                ))
            except commands.ExtensionNotLoaded:
                try:
                    await self.bot.load_extension(cog)
                    await status_msg.edit(embed=discord.Embed(
                        title="√ loaded",
                        description=f"loaded `{cog}` (fresh)",
                        color=0x57f287
                    ))
                except Exception as e:
                    await status_msg.edit(embed=discord.Embed(
                        title="✖ failed",
                        description=f"`{cog}`: {e}",
                        color=0xff4500
                    ))
            except Exception as e:
                await status_msg.edit(embed=discord.Embed(
                    title="✖ failed",
                    description=f"`{cog}`: {e}",
                    color=0xff4500
                ))
            return

        reloaded_logs = []
        for root, dirs, files in os.walk("./commands"):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    path = os.path.relpath(os.path.join(root, file), ".").replace(os.sep, ".").removesuffix(".py")
                    try:
                        await self.bot.reload_extension(path)
                        reloaded_logs.append(f"√ `{path}`")
                    except commands.ExtensionNotLoaded:
                        try:
                            await self.bot.load_extension(path)
                            reloaded_logs.append(f"√ `{path}` (loaded fresh)")
                        except Exception as e:
                            reloaded_logs.append(f"✖ `{path}`: {e}")
                    except Exception as e:
                        reloaded_logs.append(f"✖ `{path}`: {e}")

        log_chunk = "\n".join(reloaded_logs) or "no cogs found."
        if len(log_chunk) > 4000:
            log_chunk = log_chunk[:3997] + "..."

        await status_msg.edit(embed=discord.Embed(
            title="√ reloaded",
            description=log_chunk,
            color=0x57f287
        ))

    @commands.hybrid_command(name="unload", description="unload a cog extension", help="Unload a specific extension. Usage: !unload commands.economy.bal. Admin only.")
    async def unload(self, ctx, cog: str):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized.", color=0xff4500))
        try:
            await self.bot.unload_extension(cog)
            await ctx.send(embed=discord.Embed(
                description=f"√ unloaded `{cog}`",
                color=0x57f287
            ))
        except commands.ExtensionNotLoaded:
            await ctx.send(embed=discord.Embed(
                description=f"⊘ extension `{cog}` is not loaded.",
                color=0xff4500
            ))

    @commands.hybrid_command(name="cogs", aliases=["extensions"], description="list all loaded cogs", help="Shows all currently loaded bot extensions. Admin only.")
    async def list_cogs(self, ctx):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized.", color=0xff4500))
        extensions = sorted(self.bot.extensions.keys())
        if not extensions:
            return await ctx.send("no cogs loaded.")
        chunks = [extensions[i:i + 20] for i in range(0, len(extensions), 20)]
        for chunk in chunks:
            await ctx.send(embed=discord.Embed(
                title="loaded cogs",
                description="\n".join(f"`{e}`" for e in chunk),
                color=0x2b2d31
            ))

async def setup(bot) -> None:
    await bot.add_cog(Admin(bot))