"""Static analysis checks for codebase-wide patterns:
  - deprecated @commands.command() usage (should be hybrid_command)
  - setup() functions missing -> None return type
  - bare except: clauses
  - potential missing awaits on async methods
  - bare config key access patterns
"""
import ast
import os
import re


COMMANDS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "commands"))
IGNORE_DIRS = {"__pycache__"}

issues = []


def _py_files():
    for root, dirs, files in os.walk(COMMANDS_DIR):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(root, f)


def check_old_command_decorator(filepath: str, tree: ast.Module):
    """Flag @commands.command() -- should be @commands.hybrid_command()"""
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "command":
                if isinstance(func.value, ast.Attribute) and func.value.attr == "commands":
                    issues.append((filepath, node.lineno, "use @commands.hybrid_command() instead of @commands.command()"))


def check_setup_return_type(filepath: str, tree: ast.Module):
    """Flag 'async def setup(bot):' without '-> None'"""
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "setup":
            if node.returns is None:
                issues.append((filepath, node.lineno, "setup() missing -> None return type"))


def check_bare_except(filepath: str, tree: ast.Module):
    """Flag bare 'except:' clauses (should be 'except Exception:')"""
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                issues.append((filepath, node.lineno, "bare except: -- use 'except Exception:'"))


def check_potential_missing_await(filepath: str, tree: ast.Module):
    """Flag calls to async methods without await inside async functions.
    Only flags if the target method is actually defined as async in the same file."""
    async_methods = set()
    sync_methods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            async_methods.add(node.name)
        elif isinstance(node, ast.FunctionDef):
            sync_methods.add(node.name)

    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            for child in ast.walk(node):
                if isinstance(child, ast.Expr) and isinstance(child.value, ast.Call):
                    call = child.value
                    if isinstance(call.func, ast.Attribute):
                        name = call.func.attr
                        if name in async_methods and name not in sync_methods:
                            if not isinstance(child.value, ast.Await):
                                issues.append((filepath, child.lineno,
                                               f"missing await on '{name}' -- async call result discarded"))


def check_config_key_access(filepath: str, tree: ast.Module):
    """Flag bare cfg[key] access without .get() fallback inside config lookups"""
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
    except (UnicodeDecodeError, OSError):
        try:
            with open(filepath, encoding="latin-1") as f:
                content = f.read()
        except OSError:
            return
    pattern = re.findall(r'_cfg\[\s*["\'](\w+)["\']\s*\]', content)
    if pattern:
        issues.append((filepath, 0, f"bare config key access: {', '.join(pattern)} -- use .get()"))


def run_all():
    for fp in _py_files():
        try:
            with open(fp, encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source, filename=fp)
            check_old_command_decorator(fp, tree)
            check_setup_return_type(fp, tree)
            check_bare_except(fp, tree)
            check_potential_missing_await(fp, tree)
            check_config_key_access(fp, tree)
        except SyntaxError as e:
            issues.append((fp, e.lineno or 0, f"syntax error: {e}"))

    return issues


def has_issues() -> bool:
    issues.clear()
    run_all()
    return len(issues) > 0


def print_report():
    issues.clear()
    run_all()
    if not issues:
        print("  [OK] no consistency issues found")
        return

    by_file = {}
    for fp, lineno, msg in issues:
        by_file.setdefault(fp, []).append((lineno, msg))

    for fp, items in sorted(by_file.items()):
        rel = os.path.relpath(fp, os.path.dirname(COMMANDS_DIR))
        print(f"\n  {rel}")
        for lineno, msg in sorted(items):
            line = f"    l{lineno}" if lineno else "    --"
            print(f"  {line}  {msg}")


if __name__ == "__main__":
    print_report()
