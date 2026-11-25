#!/usr/bin/env python3
"""Issue #110: no shipped script uses a name it never imports or defines.

launch.py called `platform_paths.venv_python(...)` inside functions without
importing `platform_paths`.  Importing the module does not trip that -- the call
sits in a function body -- so this reads every shipped .py and flags a name that
is loaded somewhere but bound nowhere in the file and is not a builtin.  Stdlib
only.  A file that cannot even be compiled fails too.

The check must be able to fail: it is also run on the launch.py of 1.10.0 (the
import line removed) and must flag `platform_paths` there.

    python checks/update/check_shipped_scripts.py
"""

from __future__ import annotations

import ast
import builtins
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC = REPO / "src"
LAUNCH = SRC / ".claude" / "skills" / "transcribe" / "scripts" / "launch.py"
IMPORT_LINE = "import platform_paths"

_BUILTINS = set(dir(builtins)) | {"__file__", "__name__", "__doc__", "__spec__"}


def undefined_names(source: str, filename: str = "<src>") -> list[str]:
    """Names read in *source* that nothing in it binds and no builtin supplies."""
    tree = ast.parse(source, filename)
    bound: set[str] = set()
    loaded: dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Load):
                loaded.setdefault(node.id, node.lineno)
            else:
                bound.add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(node.name)
            if not isinstance(node, ast.ClassDef):
                a = node.args
                for arg in [*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg]:
                    if arg:
                        bound.add(arg.arg)
        elif isinstance(node, ast.Lambda):
            a = node.args
            for arg in [*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg]:
                if arg:
                    bound.add(arg.arg)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                bound.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, ast.ExceptHandler) and node.name:
            bound.add(node.name)
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            bound.update(node.names)
        elif isinstance(node, ast.MatchAs) and node.name:
            bound.add(node.name)
        elif isinstance(node, ast.MatchStar) and node.name:
            bound.add(node.name)
    return sorted(n for n in loaded if n not in bound and n not in _BUILTINS)


def main() -> int:
    results: list[tuple[str, bool, str]] = []

    files = sorted(p for p in SRC.rglob("*.py") if "__pycache__" not in p.parts)
    results.append(("setup: shipped .py files found", len(files) > 0, str(len(files))))
    for path in files:
        rel = path.relative_to(REPO).as_posix()
        try:
            missing = undefined_names(path.read_text(encoding="utf-8"), rel)
        except SyntaxError as exc:
            results.append((f"{rel} compiles", False, str(exc)))
            continue
        results.append(
            (f"{rel} uses only names it binds", not missing, ", ".join(missing))
        )

    # The check must fail when the bug is present.
    text = LAUNCH.read_text(encoding="utf-8")
    broken = "\n".join(l for l in text.splitlines() if IMPORT_LINE not in l)
    results.append(
        (
            "mutation: launch.py without its platform_paths import is flagged",
            "platform_paths" in undefined_names(broken),
            "",
        )
    )
    results.append(
        (
            "AC 1  launch.py imports platform_paths",
            IMPORT_LINE in text and "platform_paths" not in undefined_names(text),
            "",
        )
    )

    for name, ok, detail in results:
        print(
            f"[{'PASS' if ok else 'FAIL'}] {name}"
            + (f"  -- {detail}" if not ok and detail else "")
        )
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n#110: {passed}/{len(results)} checks pass.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
