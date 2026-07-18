import discord
from discord.ext import commands
from collections import defaultdict, deque
from helpers.config import get_channel_id, get_guild_id

LOG_CHANNEL = get_channel_id("log")
CONSOLE_CHANNEL = get_channel_id("console")
GUILD_ID = get_guild_id()

class Logger(commands.Cog):
    PERMISSION_NAMES = [
        "create_instant_invite","kick_members","ban_members","administrator",
        "manage_channels","manage_guild","add_reactions","view_audit_log",
        "priority_speaker","stream","view_channel","send_messages",
        "send_tts_messages","manage_messages","embed_links","attach_files",
        "read_message_history","mention_everyone","use_external_emojis",
        "view_guild_insights","connect","speak","mute_members","deafen_members",
        "move_members","use_vad","change_nickname","manage_nicknames",
        "manage_roles","manage_webhooks","manage_emojis_and_stickers",
        "use_application_commands","request_to_speak","manage_events",
        "manage_threads","create_public_threads","create_private_threads",
        "use_external_stickers","send_messages_in_threads",
        "use_embedded_activities","moderate_members","send_voice_messages",
    ]

    MAX_STATS_ENTRIES = 500

    def __init__(self, bot) -> None:
        self.bot = bot
        self.cmd_usage = defaultdict(int)
        self.user_usage = defaultdict(int)
        self.deleted_cache = deque(maxlen=100)

    async def log(self, guild, embed):
        if not guild or guild.id != GUILD_ID:
            return
        ch = guild.get_channel(LOG_CHANNEL)
        if ch:
            await ch.send(embed=embed)

    def _get_permission_diff(self, before, after):
        changes = []
        for perm in self.PERMISSION_NAMES:
            try:
                b_val = getattr(before.permissions, perm)
                a_val = getattr(after.permissions, perm)
                if b_val != a_val:
                    changes.append(f"{'+'  if a_val else '-'} {perm.replace('_', ' ')}")
            except AttributeError:
                continue
        return changes

    def _get_overwrite_diff(self, before_ow, after_ow):
        changes = []
        for perm in self.PERMISSION_NAMES:
            try:
                b_val = getattr(before_ow, perm, None)
                a_val = getattr(after_ow, perm, None)
                if b_val != a_val:
                    if a_val is True:
                        changes.append(f"+ {perm.replace('_', ' ')}")
                    elif a_val is False:
                        changes.append(f"- {perm.replace('_', ' ')}")
                    elif a_val is None and b_val is not None:
                        changes.append(f"↩ {perm.replace('_', ' ')} (reset to @everyone)")
            except AttributeError:
                continue
        return changes

    @commands.Cog.listener()
    async def on_command(self, ctx):
        if not ctx.guild or ctx.guild.id != GUILD_ID:
            return
        if ctx.command:
            self.cmd_usage[ctx.command.name] += 1
            self.user_usage[ctx.author.id] += 1
            if len(self.cmd_usage) > self.MAX_STATS_ENTRIES * 2:
                self._trim_stats()

    def _trim_stats(self) -> None:
        threshold = 2
        for d in (self.cmd_usage, self.user_usage):
            for k in list(d):
                if d[k] < threshold:
                    del d[k]
            if len(d) > self.MAX_STATS_ENTRIES:
                top = sorted(d.items(), key=lambda x: x[1], reverse=True)[:self.MAX_STATS_ENTRIES]
                d.clear()
                d.update(top)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        if not ctx.guild or ctx.guild.id != GUILD_ID:
            return
        if ctx.command and ctx.command.name == "eval":
            raw = ctx.message.content
            parts = raw.split(" ", 1)
            code = parts[1] if len(parts) > 1 else "*no code*"
            embed = discord.Embed(title="⚙ eval used", color=0x5865f2, timestamp=discord.utils.utcnow())
            embed.add_field(name="user", value=ctx.author.mention)
            embed.add_field(name="channel", value=ctx.channel.mention)
            embed.add_field(name="input", value=f"```\n{code[:1000]}\n```", inline=False)
            await self.log(ctx.guild, embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild or message.guild.id != GUILD_ID:
            return
        if message.channel.id == CONSOLE_CHANNEL:
            embed = discord.Embed(title="🖥 console input", color=0x2b2d31, timestamp=discord.utils.utcnow())
            embed.add_field(name="user", value=message.author.mention)
            embed.add_field(name="input", value=f"```\n{message.content[:1000]}\n```", inline=False)
            await self.log(message.guild, embed)

    @commands.hybrid_command(description="show command usage statistics", help="Shows the top 5 most used commands and top 5 most active users.")
    async def stats(self, ctx):
        if ctx.guild.id != GUILD_ID:
            return
        top_cmds = sorted(self.cmd_usage.items(), key=lambda x: x[1], reverse=True)[:5]
        top_users = sorted(self.user_usage.items(), key=lambda x: x[1], reverse=True)[:5]
        embed = discord.Embed(color=0x5865f2)
        embed.add_field(name="◈ top commands", value="\n".join(f"{k}: {v}" for k, v in top_cmds) or "none", inline=False)
        embed.add_field(name="◈ top users", value="\n".join(f"<@{k}>: {v}" for k, v in top_users) or "none", inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(description="restore the last deleted message", help="Resends the most recently deleted message in the current channel, including attachments.")
    async def restore(self, ctx):
        if ctx.guild.id != GUILD_ID:
            return
        if not self.deleted_cache:
            return await ctx.send("nothing to restore")
        msg = self.deleted_cache[-1]
        content = msg["content"] or "*no content*"
        try:
            files = [await a.to_file() for a in msg["attachments"]]
        except Exception:
            files = []
        await ctx.send(content=content, files=files if files else None)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or not before.guild or before.guild.id != GUILD_ID:
            return
        if before.content == after.content:
            return
        embed = discord.Embed(title="✏ message edited", color=0xf1c40f, timestamp=discord.utils.utcnow())
        embed.add_field(name="user", value=before.author.mention)
        embed.add_field(name="channel", value=before.channel.mention)
        embed.add_field(name="before", value=before.content[:1000] or "*[no content]*", inline=False)
        embed.add_field(name="after", value=after.content[:1000] or "*[no content]*", inline=False)
        await self.log(before.guild, embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.guild or message.guild.id != GUILD_ID or message.author.bot:
            return
        self.deleted_cache.append({"content": message.content, "attachments": message.attachments})
        embed = discord.Embed(title="🗑 message deleted", color=0xff4500, timestamp=discord.utils.utcnow())
        embed.add_field(name="user", value=message.author.mention)
        embed.add_field(name="channel", value=message.channel.mention)
        if message.content:
            embed.add_field(name="content", value=message.content[:1000], inline=False)
        if message.attachments:
            embed.add_field(name="attachments", value="\n".join(a.url for a in message.attachments), inline=False)
        await self.log(message.guild, embed)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        if not messages or not messages[0].guild or messages[0].guild.id != GUILD_ID:
            return
        embed = discord.Embed(title="🗑 bulk delete", color=0xff4500, timestamp=discord.utils.utcnow())
        embed.add_field(name="count", value=str(len(messages)))
        embed.add_field(name="channel", value=messages[0].channel.mention)
        await self.log(messages[0].guild, embed)

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry):
        if entry.guild.id != GUILD_ID:
            return
        if entry.action == discord.AuditLogAction.ban:
            embed = discord.Embed(title="🔨 user banned", color=0xff4500, timestamp=discord.utils.utcnow())
            embed.add_field(name="user", value=str(entry.target))
            embed.add_field(name="moderator", value=str(entry.user))
            if entry.reason:
                embed.add_field(name="reason", value=entry.reason, inline=False)
            await self.log(entry.guild, embed)
        elif entry.action == discord.AuditLogAction.unban:
            embed = discord.Embed(title="🔓 user unbanned", color=0x57f287, timestamp=discord.utils.utcnow())
            embed.add_field(name="user", value=str(entry.target))
            embed.add_field(name="moderator", value=str(entry.user))
            await self.log(entry.guild, embed)
        elif entry.action == discord.AuditLogAction.kick:
            embed = discord.Embed(title="👢 user kicked", color=0xff4500, timestamp=discord.utils.utcnow())
            embed.add_field(name="user", value=str(entry.target))
            embed.add_field(name="moderator", value=str(entry.user))
            if entry.reason:
                embed.add_field(name="reason", value=entry.reason, inline=False)
            await self.log(entry.guild, embed)
        elif entry.action == discord.AuditLogAction.member_role_update:
            embed = discord.Embed(title="✏ roles updated", color=0xf1c40f, timestamp=discord.utils.utcnow())
            embed.add_field(name="user", value=str(entry.target))
            embed.add_field(name="moderator", value=str(entry.user))
            try:
                after = entry.changes.after.roles if entry.changes else []
                before = entry.changes.before.roles if entry.changes else []
                added = [r for r in after if r not in before]
                removed = [r for r in before if r not in after]
                if added:
                    embed.add_field(name="roles added", value=", ".join(r.name for r in added), inline=False)
                if removed:
                    embed.add_field(name="roles removed", value=", ".join(r.name for r in removed), inline=False)
            except Exception:
                pass
            await self.log(entry.guild, embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        if guild.id != GUILD_ID:
            return
        embed = discord.Embed(title="🔓 user unbanned", color=0x57f287)
        embed.add_field(name="user", value=str(user))
        await self.log(guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        embed = discord.Embed(title="➕ role created", color=0x57f287)
        embed.add_field(name="role", value=role.mention)
        await self.log(role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        embed = discord.Embed(title="➖ role deleted", color=0xff4500)
        embed.add_field(name="role", value=role.name)
        await self.log(role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        embed = discord.Embed(title="✏ role updated", color=0xf1c40f, timestamp=discord.utils.utcnow())
        changed = False
        if before.name != after.name:
            embed.add_field(name="name", value=f"{before.name} → {after.name}", inline=False)
            changed = True
        perm_changes = self._get_permission_diff(before, after)
        if perm_changes:
            embed.add_field(name="permissions", value="\n".join(perm_changes[:25]), inline=False)
            changed = True
        if changed:
            await self.log(after.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if before.guild.id != GUILD_ID:
            return
        embed = discord.Embed(title="📡 channel updated", color=0xf1c40f, timestamp=discord.utils.utcnow())
        embed.add_field(name="channel", value=after.mention, inline=False)
        changed = False
        if before.name != after.name:
            embed.add_field(name="name", value=f"{before.name} → {after.name}", inline=False)
            changed = True
        before_overwrites = dict(before.overwrites)
        after_overwrites = dict(after.overwrites)
        for target, after_perm in after_overwrites.items():
            target_str = target.mention if hasattr(target, "mention") else getattr(target, "name", f"id:{target.id}")
            if target not in before_overwrites:
                embed.add_field(name=f"➕ new permissions for {target_str}", value="overridden (check audit log)", inline=False)
                changed = True
            else:
                perm_changes = self._get_overwrite_diff(before_overwrites[target], after_perm)
                if perm_changes:
                    embed.add_field(name=f"✏ permissions updated for {target_str}", value="\n".join(perm_changes[:20]), inline=False)
                    changed = True
        for target in list(before_overwrites.keys()):
            if target not in after_overwrites:
                target_str = target.mention if hasattr(target, "mention") else getattr(target, "name", f"id:{target.id}")
                embed.add_field(name=f"➖ permissions removed for {target_str}", value="reset to @everyone", inline=False)
                changed = True
        if changed:
            await self.log(after.guild, embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.guild.id != GUILD_ID or before.channel == after.channel:
            return
        embed = discord.Embed(color=0x5865f2)
        embed.add_field(name="user", value=member.mention)
        if before.channel is None:
            embed.title = "🔊 joined voice"
            embed.add_field(name="channel", value=after.channel.mention if after.channel else "unknown")
        elif after.channel is None:
            embed.title = "🔇 left voice"
            embed.add_field(name="channel", value=before.channel.mention if before.channel else "unknown")
        else:
            embed.title = "🔁 moved voice"
            embed.add_field(name="from", value=before.channel.mention if before.channel else "unknown")
            embed.add_field(name="to", value=after.channel.mention if after.channel else "unknown")
        await self.log(member.guild, embed)

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        embed = discord.Embed(title="🧵 thread created", color=0x57f287)
        embed.add_field(name="thread", value=thread.mention)
        await self.log(thread.guild, embed)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        embed = discord.Embed(title="🧵 thread deleted", color=0xff4500)
        embed.add_field(name="name", value=thread.name)
        await self.log(thread.guild, embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id != GUILD_ID:
            return
        embed = discord.Embed(title="👋 member joined", color=0x57f287, timestamp=discord.utils.utcnow())
        embed.add_field(name="user", value=member.mention)
        await self.log(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.guild.id != GUILD_ID:
            return
        embed = discord.Embed(title="🚪 member left", color=0xff4500, timestamp=discord.utils.utcnow())
        embed.add_field(name="user", value=str(member))
        await self.log(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.guild.id != GUILD_ID:
            return
        embed = discord.Embed(title="✏ member updated", color=0xf1c40f, timestamp=discord.utils.utcnow())
        embed.add_field(name="user", value=before.mention)
        changed = False
        if before.nick != after.nick:
            embed.add_field(name="nickname", value=f"{before.nick or '*none*'} → {after.nick or '*none*'}", inline=False)
            changed = True
        if before.roles != after.roles:
            added = [r.mention for r in after.roles if r not in before.roles and not r.is_default()]
            removed = [r.mention for r in before.roles if r not in after.roles and not r.is_default()]
            if added:
                embed.add_field(name="roles added", value=", ".join(added), inline=False)
                changed = True
            if removed:
                embed.add_field(name="roles removed", value=", ".join(removed), inline=False)
                changed = True
        if changed:
            await self.log(before.guild, embed)

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        if before.id != GUILD_ID:
            return
        embed = discord.Embed(title="🏠 guild updated", color=0xf1c40f, timestamp=discord.utils.utcnow())
        changed = False
        if before.name != after.name:
            embed.add_field(name="name", value=f"{before.name} → {after.name}", inline=False)
            changed = True
        if before.icon != after.icon:
            embed.add_field(name="icon", value="changed" if after.icon else "removed", inline=False)
            changed = True
        if changed:
            await self.log(after, embed)

async def setup(bot) -> None:
    await bot.add_cog(Logger(bot))
