import discord
import asyncio
import io
import os
import sys
import traceback
import yaml
from discord.ext import commands
from helpers.admins_config import is_admin

MAX_EMBED = 4000

def _load_cfg():
    path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "config.yaml"))
    with open(path) as f:
        return yaml.safe_load(f)

_cfg = _load_cfg()
CONSOLE_CHANNEL_ID = _cfg["channels"]["console"]

def _truncate(text: str) -> str:
    if len(text) <= MAX_EMBED:
        return text
    half = (MAX_EMBED - 20) // 2
    return text[:half] + "\n...[truncated]...\n" + text[-half:]

class Eval(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _run_code(self, ctx, code: str):
        code = code.strip().strip("```").removeprefix("python").removeprefix("py").strip()
        msg = await ctx.send(embed=discord.Embed(description="⧖ running...", color=0x2b2d31))
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        shell_out = ""
        py_error = ""
        try:
            proc = await asyncio.create_subprocess_shell(
                code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
            shell_out = (stdout.decode() + stderr.decode()).strip()
            success = proc.returncode == 0
        except asyncio.TimeoutError:
            shell_out = "⊘ timed out after 60s"
            success = False
        except Exception:
            shell_out = None
        if shell_out is None:
            old_stdout, old_stderr = sys.stdout, sys.stderr
            sys.stdout, sys.stderr = stdout_buf, stderr_buf
            try:
                exec(compile(code, "<eval>", "exec"), {"bot": self.bot, "ctx": ctx, "discord": discord})
                success = True
            except Exception:
                py_error = traceback.format_exc()
                success = False
            finally:
                sys.stdout, sys.stderr = old_stdout, old_stderr
            shell_out = (stdout_buf.getvalue() + stderr_buf.getvalue()).strip()
            if py_error:
                shell_out = (shell_out + "\n" + py_error).strip()
        output = _truncate(shell_out) if shell_out else "*(no output)*"
        color = 0x57f287 if success else 0xff4500
        embed = discord.Embed(color=color)
        embed.add_field(name="◈ input", value=f"```\n{code[:900]}\n```", inline=False)
        embed.add_field(name="◈ output", value=f"```\n{output}\n```", inline=False)
        embed.set_footer(text=f"exit {'0' if success else '1'}")
        await msg.edit(embed=embed)

    @commands.hybrid_command(name="eval")
    async def eval_cmd(self, ctx, *, code: str):
        if not is_admin(ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="⊘ unauthorized.", color=0xff4500))
        await self._run_code(ctx, code)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.channel.id != CONSOLE_CHANNEL_ID:
            return
        if not is_admin(message.author.id):
            return
        ctx = await self.bot.get_context(message)
        await self._run_code(ctx, message.content)

    @eval_cmd.error
    async def eval_error(self, ctx, error):
        error.handled = True
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(description="⊘ usage: `!eval <code or shell command>`", color=0xff4500))

async def setup(bot) -> None:
    await bot.add_cog(Eval(bot))
