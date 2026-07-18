import asyncio
import discord
import os
import signal
import sys
from discord.ext import commands
from dotenv import load_dotenv
from helpers.config import load_config
from helpers.logging import init as init_logging
from helpers.economy_base import check_ratelimit, RATE_LIMIT_COMMANDS, RATE_LIMIT_WINDOW
from helpers.blacklist_config import is_blacklisted

load_dotenv()

REQUIRED_ENV = {
    "DISCORD_TOKEN": "Discord bot token",
    "GROQ_KEY": "Groq API key (AI chat, gambling commentary)",
    "OPENWEATHER_KEY": "OpenWeatherMap API key (!weather)",
}

MISSING = [f"{k} ({v})" for k, v in REQUIRED_ENV.items() if not os.getenv(k)]
if MISSING:
    msg = "missing required environment variables:\n" + "\n".join(f"  ✖ {m}" for m in MISSING)
    msg += "\n\ncopy .env.example to .env and fill in the values."
    raise SystemExit(msg)

TOKEN = os.getenv('DISCORD_TOKEN')
log = init_logging()

# Validate config
try:
    cfg = load_config()
    guild_id = cfg.get("guild_id")
    if not guild_id:
        raise SystemExit("✖ config.yaml: guild_id is required")
    channels = cfg.get("channels", {})
    for ch in ("log", "console", "ai_chat", "dictionary", "confession", "hall_of_fame", "welcome"):
        if ch not in channels:
            log.warning("config.yaml: missing channel '%s' — set it at runtime", ch)
except Exception as e:
    raise SystemExit(f"✖ config.yaml error: {e}")

ALLOWED_GUILD_ID = guild_id

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.moderation = True

BANNER = r"""
  __  __      _       ____
 |  \/  |    | |     / ___|___  _ __ ___
 | |\/| |/ _` |_   _| |   / _ \| '__/ _ \
 | |  | | (_| | |_| | |__| (_) | | |  __/
 |_|  |_|\__,_|\__, |\____\___/|_|  \___|
               |___/
"""

class M4Core(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None,
        )

    async def setup_hook(self):
        await super().setup_hook()

        async def globally_block_other_guilds(ctx):
            if ctx.guild is None:
                return ctx.command and ctx.command.name in ("confess",)
            return ctx.guild.id == ALLOWED_GUILD_ID

        async def check_blacklist(ctx):
            if is_blacklisted(ctx.author.id):
                raise commands.CheckFailure("⊘ you are blacklisted from using commands.")
            return True

        async def typing_indicator(ctx):
            await ctx.channel.trigger_typing()

        async def economy_ratelimit(ctx):
            if ctx.command and ctx.command.cog and ctx.command.cog.qualified_name in (
                "Balance", "Work", "Beg", "Crime", "Daily", "Coinflip",
                "Blackjack", "Plinko", "Transfers", "Codes", "Stats",
            ):
                if check_ratelimit(ctx.author.id):
                    raise commands.CheckFailure(
                        f"⊘ slow down! max {RATE_LIMIT_COMMANDS} commands per {RATE_LIMIT_WINDOW}s"
                    )
            return True

        self.add_check(globally_block_other_guilds)
        self.add_check(check_blacklist)
        self.before_invoke(typing_indicator)
        self.add_check(economy_ratelimit)

        loaded = 0
        failed = 0
        failed_list: list[str] = []
        for root, dirs, files in os.walk("./commands"):
            for filename in files:
                if filename.endswith(".py") and filename != "__init__.py":
                    relative_path = os.path.relpath(os.path.join(root, filename), ".")
                    module_path = relative_path.replace(os.sep, ".").removesuffix(".py")
                    try:
                        await self.load_extension(module_path)
                        loaded += 1
                    except Exception as e:
                        log.error("failed to load %s: %s", module_path, e)
                        failed += 1
                        failed_list.append(module_path)

        cmd_count = len(self.commands)
        print(BANNER)
        log.info("loaded %d cogs · %d commands · %d failed", loaded, cmd_count, failed)
        if failed_list:
            log.warning("failed modules: %s", ", ".join(failed_list))

        try:
            from safety.checks import run_all
            s_errors, s_warnings = run_all()
            for w in s_warnings:
                log.warning("safety: %s", w)
            for e in s_errors:
                log.error("safety: %s", e)
            if not s_errors:
                log.info("safety checks passed")
        except Exception as e:
            log.warning("safety checks skipped: %s", e)

    async def on_ready(self):
        print(BANNER)
        log.info("logged in as %s (id: %s)", self.user, self.user.id)
        log.info("serving %d guilds · %d commands", len(self.guilds), len(self.commands))
        if not hasattr(self, "_synced"):
            await self.tree.sync(guild=discord.Object(id=ALLOWED_GUILD_ID))
            self._synced = True
            log.info("slash commands synced")

    async def close(self) -> None:
        log.info("shutting down gracefully...")
        await super().close()

    async def on_command_error(self, ctx, error):
        if hasattr(error, 'handled'):
            return
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(embed=discord.Embed(
                title="✖ unknown command",
                description="that command doesn't exist! try !help to see commands",
                color=discord.Color.red()
            ))
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=discord.Embed(
                title="✖ missing permissions",
                description="you don't have the required permissions to use this!",
                color=discord.Color.red()
            ))
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(
                title="✖ missing argument",
                description=f"`{error.param.name}` is required but was not provided!",
                color=discord.Color.red()
            ))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(embed=discord.Embed(
                title="✖ bad argument",
                description="one or more arguments are invalid!",
                color=discord.Color.red()
            ))
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(embed=discord.Embed(
                description=f"⧖ cooldown: try again in `{error.retry_after:.0f}s`",
                color=0xf1c40f
            ), delete_after=5)
        elif isinstance(error, commands.CheckFailure):
            msg = str(error) or "⊘ you don't have permission to use this command."
            embed = discord.Embed(description=msg, color=0xff4500)
            await ctx.send(embed=embed, delete_after=5)
        else:
            log.error("unhandled error in %s: %s", ctx.command or "?", error)
            await ctx.send(embed=discord.Embed(
                description="⊘ an unexpected error occurred. the bot owner has been notified.",
                color=0xff4500
            ), delete_after=5)

def _check_legacy_and_migrate():
    from safety.checks import find_legacy_msgpack, run_migration
    legacy = find_legacy_msgpack()
    if not legacy:
        return

    print(BANNER)
    print("  ┌─────────────────────────────────────────────────────┐")
    print("  │  LEGACY MSGPACK DATA DETECTED                       │")
    print("  │  The bot now uses SQLite instead of msgpack files.  │")
    print("  │                                                     │")
    print(f"  │  {len(legacy)} file(s) found in data/ directory:              │")
    for name in legacy:
        print(f"  │    • {name:<51}│")
    print("  │                                                     │")
    print("  │  These will be migrated to data/m4.db and renamed   │")
    print("  │  to *.bak on completion.                            │")
    print("  └─────────────────────────────────────────────────────┘")
    print()

    try:
        answer = input("  Migrate legacy data now? (y/N): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        answer = "n"
    print()

    if answer == "y":
        print("  running migration...\n")
        ok = run_migration()
        if ok:
            print("\n  migration complete, starting bot.\n")
        else:
            print("\n  migration failed — check errors above. starting bot with existing data.\n")
    else:
        print("  skipping migration. run 'python -m safety.migrate_msgpack' manually.\n")


bot = M4Core()

if __name__ == "__main__":
    _check_legacy_and_migrate()

    if sys.platform != "win32":
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(
                    bot.close()
                ))
            except NotImplementedError:
                signal.signal(sig, lambda s, f: asyncio.create_task(bot.close()))

    try:
        bot.run(TOKEN)
    except KeyboardInterrupt:
        log.info("keyboard interrupt — shutting down")
    except Exception as e:
        log.critical("fatal error: %s", e)
        raise