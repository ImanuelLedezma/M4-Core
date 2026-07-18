import ast
import math
import operator
import discord
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType

SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

SAFE_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
    "inf": math.inf,
    "nan": math.nan,
}

SAFE_FUNCS = {
    "sqrt": math.sqrt, "abs": abs, "round": round,
    "floor": math.floor, "ceil": math.ceil,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "log": math.log, "log10": math.log10, "log2": math.log2,
    "exp": math.exp, "factorial": math.factorial,
    "degrees": math.degrees, "radians": math.radians,
}

def _safe_eval(node):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in SAFE_CONSTANTS:
            return SAFE_CONSTANTS[node.id]
        raise ValueError(f"unknown constant: {node.id}")
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in SAFE_FUNCS:
            raise ValueError(f"unknown function: {getattr(node.func, 'id', '?')}")
        args = [_safe_eval(a) for a in node.args]
        return SAFE_FUNCS[node.func.id](*args)
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"unsupported operator: {op_type.__name__}")
        return SAFE_OPERATORS[op_type](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"unsupported operator: {op_type.__name__}")
        return SAFE_OPERATORS[op_type](_safe_eval(node.operand))
    raise ValueError(f"unsupported syntax: {type(node).__name__}")

class Calculator(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="calculator", aliases=["calc"], description="evaluate a math expression", help="Evaluate a math expression. Supports: + - * / ^ sqrt() sin() cos() tan() log() abs() round() floor() ceil() pi e. Example: !calc 2+2, !calc sqrt(144), !calc pi*5^2")
    @cooldown(1, 2, BucketType.user)
    async def calculator(self, ctx, *, expression: str):
        clean = expression.replace('x', '*').replace('X', '*').replace('×', '*')

        try:
            tree = ast.parse(clean, mode="eval")
            result = _safe_eval(tree.body)

            embed = discord.Embed(title="calculator", color=discord.Color.blue())
            embed.add_field(name="input", value=f"```\n{expression}\n```", inline=False)
            embed.add_field(name="result", value=f"```\n{result}\n```", inline=False)
            await ctx.send(embed=embed)

        except (SyntaxError, ValueError, TypeError, OverflowError):
            await ctx.send(embed=discord.Embed(
                title="✖ invalid expression",
                description="use numbers and operators only. (e.g. `4*2`, `10/2`, `sqrt(9)`)",
                color=discord.Color.red()
            ))

async def setup(bot) -> None:
    await bot.add_cog(Calculator(bot))