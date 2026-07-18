import asyncio
import discord
from discord.ext import commands
from collections import OrderedDict

COG_MAP = {
    "commands.general": "general",
    "commands.utility": "utility",
    "commands.moderation": "moderation",
    "commands.economy": "economy",
    "commands.fun": "fun",
    "commands.events": "events",
    "commands.maintenance": "maintenance",
}

CATEGORY_META = {
    "general":     {"emoji": "⚙", "label": "general"},
    "utility":     {"emoji": "🧰", "label": "utility"},
    "moderation":  {"emoji": "🛡", "label": "moderation"},
    "economy":     {"emoji": "⌬", "label": "economy"},
    "fun":         {"emoji": "🎲", "label": "fun"},
    "events":      {"emoji": "📡", "label": "events"},
    "maintenance": {"emoji": "⚡", "label": "maintenance"},
}

CATEGORY_ORDER = ["general", "utility", "moderation", "economy", "fun", "events", "maintenance"]
COMMANDS_PER_PAGE = 15

class Help(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    def _get_category(self, cmd) -> str:
        if not cmd.cog:
            return "other"
        module = cmd.cog.__class__.__module__
        parts = module.split(".")
        prefix = f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else module
        return COG_MAP.get(prefix, "other")

    def _build_pages(self, bot) -> list[discord.Embed]:
        grouped: dict[str, list[str]] = OrderedDict()
        for cmd in sorted(bot.commands, key=lambda c: c.qualified_name):
            if not cmd.cog:
                continue
            cat = self._get_category(cmd)
            if cat not in grouped:
                grouped[cat] = []
            entry = f"`!{cmd.qualified_name}"
            if cmd.signature:
                entry += f" {cmd.signature}"
            entry += "`"
            if cmd.description:
                entry += f" · {cmd.description}"
            grouped[cat].append(entry)

        pages: list[discord.Embed] = []
        page_entries: list[str] = []

        for cat in CATEGORY_ORDER:
            if cat not in grouped:
                continue
            meta = CATEGORY_META.get(cat, {"emoji": "◈", "label": cat})
            label = f"{meta['emoji']} {meta['label'].upper()}" if cat == "maintenance" else f"{meta['emoji']} {meta['label']}"
            if cat == "maintenance":
                label += " ⌠auth⌡"
            page_entries.append(f"\n**{label}**\n")
            for cmd_entry in grouped[cat]:
                page_entries.append(cmd_entry)

        chunks = [page_entries[i:i + COMMANDS_PER_PAGE] for i in range(0, len(page_entries), COMMANDS_PER_PAGE)]
        total = len(chunks)

        for idx, chunk in enumerate(chunks):
            embed = discord.Embed(
                title="╼ m4-core systems ╾",
                description="prefix: `!` · currency: `cores`\nuse `!help <command>` for details",
                color=0x5865f2
            )
            field_buffer = ""
            for line in chunk:
                if len(field_buffer) + len(line) + 1 > 1024:
                    embed.add_field(
                        name=f"page {idx + 1}/{total}" if total > 1 else "commands",
                        value=field_buffer,
                        inline=False
                    )
                    field_buffer = line + "\n"
                else:
                    field_buffer += line + "\n"
            if field_buffer:
                embed.add_field(
                    name=f"page {idx + 1}/{total}" if total > 1 else "commands",
                    value=field_buffer,
                    inline=False
                )
            embed.set_footer(text="⧖ = cooldown · ⌬ = cores · ⌠perm⌡ = requires permission · ⌠auth⌡ = authorized only")
            pages.append(embed)

        return pages

    def _command_help_embed(self, cmd: commands.Command) -> discord.Embed:
        cat = self._get_category(cmd)
        meta = CATEGORY_META.get(cat, {"emoji": "◈", "label": cat})
        cat_label = f"{meta['emoji']} {meta['label']}"

        aliases = "`, `".join(cmd.aliases) if cmd.aliases else "none"
        usage = f"`!{cmd.qualified_name}"
        if cmd.signature:
            usage += f" {cmd.signature}"
        usage += "`"

        perms = []
        if cmd.checks:
            for check in cmd.checks:
                try:
                    if hasattr(check, "__wrapped__"):
                        check = check.__wrapped__
                    name = getattr(check, "__name__", str(check))
                    perms.append(name.replace("_", " "))
                except Exception:
                    pass
        perm_str = "`, `".join(perms) if perms else "none"

        embed = discord.Embed(
            title=f"`!{cmd.qualified_name}`",
            description=cmd.description or "no description",
            color=0x5865f2
        )
        embed.add_field(name="category", value=cat_label, inline=True)
        embed.add_field(name="usage", value=usage, inline=False)
        embed.add_field(name="aliases", value=f"`{aliases}`", inline=True)
        embed.add_field(name="permissions", value=f"`{perm_str}`", inline=True)
        if cmd.help:
            embed.add_field(name="help", value=cmd.help[:1024], inline=False)
        if cmd.parent:
            embed.add_field(name="parent command", value=f"`!{cmd.parent.qualified_name}`", inline=True)
        return embed

    @commands.hybrid_command(name="help", aliases=["h", "commands"], description="view the full command list. use !help <command> for details")
    async def help(self, ctx, *, command: str = None):
        if command:
            cat_lookup = command.lower().replace("-", "_")
            if cat_lookup in CATEGORY_META:
                meta = CATEGORY_META[cat_lookup]
                grouped: dict[str, list[str]] = OrderedDict()
                for cmd in sorted(ctx.bot.commands, key=lambda c: c.qualified_name):
                    if not cmd.cog:
                        continue
                    if self._get_category(cmd) == cat_lookup:
                        grouped.setdefault(cat_lookup, [])
                        entry = f"`!{cmd.qualified_name}"
                        if cmd.signature:
                            entry += f" {cmd.signature}"
                        entry += "`"
                        if cmd.description:
                            entry += f" · {cmd.description}"
                        grouped[cat_lookup].append(entry)
                if grouped.get(cat_lookup):
                    embed = discord.Embed(
                        title=f"{meta['emoji']} {meta['label']} commands",
                        description="\n".join(grouped[cat_lookup]),
                        color=0x5865f2
                    )
                    return await ctx.send(embed=embed)

            cmd = ctx.bot.get_command(command)
            if not cmd:
                return await ctx.send(embed=discord.Embed(
                    description=f"⊘ no command or category called `{command}`. try `!help` for the list.",
                    color=0xff4500
                ))
            embed = self._command_help_embed(cmd)
            return await ctx.send(embed=embed)

        pages = self._build_pages(ctx.bot)
        if not pages:
            return await ctx.send("no commands found.")

        msg = await ctx.send(embed=pages[0])

        if len(pages) > 1:
            reactions = ["⬅️", "➡️"]
            for r in reactions:
                await msg.add_reaction(r)

            page = 0

            def check(reaction, user):
                return (
                    user.id == ctx.author.id
                    and reaction.message.id == msg.id
                    and str(reaction.emoji) in reactions
                )

            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
                    emoji = str(reaction.emoji)
                    if emoji == "➡️" and page < len(pages) - 1:
                        page += 1
                        await msg.edit(embed=pages[page])
                    elif emoji == "⬅️" and page > 0:
                        page -= 1
                        await msg.edit(embed=pages[page])
                    try:
                        await msg.remove_reaction(reaction, user)
                    except (discord.Forbidden, discord.NotFound):
                        pass
                except (asyncio.TimeoutError, Exception):
                    try:
                        await msg.clear_reactions()
                    except (discord.Forbidden, discord.NotFound):
                        pass
                    break

async def setup(bot) -> None:
    await bot.add_cog(Help(bot))