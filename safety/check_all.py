"""Run all safety checks and print a summary report."""
import importlib
import os
import sys

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))

CHECKS = [
    "check_duration_parsing",
    "check_shop_integrity",
    "check_codebase_consistency",
]

PASS = "[PASS]"
FAIL = "[FAIL]"


def main():
    passed = 0
    failed = 0
    results = []

    for name in CHECKS:
        mod = importlib.import_module(f"safety.{name}")
        verify_fns = [(k, v) for k, v in vars(mod).items()
                      if k.startswith("verify_") and callable(v)]

        if not verify_fns:
            print(f"\n  [{name}]")
            try:
                mod.print_report()
                passed += 1
                results.append((name, "pass"))
            except Exception as e:
                print(f"  {FAIL} {e}")
                failed += 1
                results.append((name, "fail"))
            continue

        module_ok = True
        print(f"\n  [{name}]")
        for fn_name, fn in verify_fns:
            try:
                fn()
                print(f"    {PASS} {fn_name.replace('verify_', '')}")
            except AssertionError as e:
                print(f"    {FAIL} {fn_name.replace('verify_', '')}: {e}")
                module_ok = False
            except Exception as e:
                print(f"    {FAIL} {fn_name.replace('verify_', '')}: {e}")
                module_ok = False

        if module_ok:
            passed += 1
            results.append((name, "pass"))
        else:
            failed += 1
            results.append((name, "fail"))

    print(f"\n  {'-' * 40}")
    print(f"  results: {passed} passed, {failed} failed out of {len(CHECKS)} checks")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
