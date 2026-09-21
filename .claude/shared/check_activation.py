#!/usr/bin/env python3
"""Issue #20 -- the daily-run half of `.claude/shared/activation.py`.

`ran_today` and `set_last_run` both default `today` via
`datetime.now().date().isoformat()`. The module imported `json` and `pathlib`
and never imported `datetime`, so every call that omitted `today` raised
`NameError`. That is every real caller: the docstring says "injectable for
tests; real callers omit it", and every existing test passed `today`
explicitly. The suite covered the branch nobody uses and never once executed
the branch everybody uses.

So the criteria here are written the other way round -- they call BOTH
functions with `today` omitted, which is the only way this bug is visible.

AC 5 is the one that matters, and it is a mutation check. It copies the
module, deletes the `datetime` import, runs the same calls against the copy in
a subprocess, and requires that run to FAIL. A check that passes both before
and after the mutation is not a check.

The repo-wide sweep is the generalisation: the bug class is "a name used at
runtime that the module never defines", and a default expression is where it
hides, because nothing executes it until a caller omits the argument.

AC 1 and AC 4 are live-boot behaviour (`/session-start` running `/news` once
and not twice). Those need a scripted-agent run and are not attempted here;
this script is the mechanism tier underneath them.

Usage: python check_activation.py
"""

from __future__ import annotations

import ast
import builtins
import importlib.util
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ACTIVATION_PY = REPO_ROOT / ".claude" / "shared" / "activation.py"
IMPORT_LINE = "from datetime import datetime\n"
SCAN_ROOTS = (
    REPO_ROOT / ".claude" / "shared",
    REPO_ROOT / ".claude" / "skills",
    REPO_ROOT / ".claude" / "hooks",
    REPO_ROOT / "tools",
)
BUILTIN_NAMES = set(dir(builtins)) | {"__file__", "__name__", "__doc__", "annotations"}

# Calls both defaults with `today` omitted. Shared by the healthy run and the
# mutated run so the two differ by exactly one line: the import.
EXERCISE = """
import importlib.util, sys
spec = importlib.util.spec_from_file_location("activation_under_test", sys.argv[1])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
record = mod.set_answer({}, "news", "1.0.0", active=True)
before = mod.ran_today(record, "news")
record = mod.set_last_run(record, "news")
after = mod.ran_today(record, "news")
stamp = mod.last_run(record, "news")
print(str(before) + "|" + str(after) + "|" + str(stamp))
"""


def load_activation():
    spec = importlib.util.spec_from_file_location("activation", ACTIVATION_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def undefined_names(path: Path) -> list[tuple[int, str]]:
    """Names loaded at runtime that the module never defines, imports or gets
    from builtins. Static, so it reaches code no test executes."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    known = set(BUILTIN_NAMES)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                known.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            known.add(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            known.add(node.id)
        elif isinstance(node, ast.arg):
            known.add(node.arg)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            known.add(node.name)
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            known.update(node.names)
    return sorted(
        {
            (n.lineno, n.id)
            for n in ast.walk(tree)
            if isinstance(n, ast.Name)
            and isinstance(n.ctx, ast.Load)
            and n.id not in known
        }
    )


def run_exercise(module_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(EXERCISE), str(module_path)],
        capture_output=True,
        text=True,
    )


def main() -> int:
    results: list[tuple[str, bool, str]] = []
    today = datetime.now().date().isoformat()
    act = load_activation()

    # --- AC 2: ran_today with no `today` answers instead of raising. ---
    record = act.set_answer({}, "news", "1.0.0", active=True)
    try:
        before = act.ran_today(record, "news")
        ac2 = before is False
        detail2 = "returned " + repr(before)
    except NameError as exc:
        ac2, detail2 = False, "raised NameError: " + str(exc)
    results.append(("AC 2: ran_today(record, 'news') with no today", ac2, detail2))

    # --- AC 3: set_last_run with no `today` stamps today's LOCAL date. ---
    stamped = None
    try:
        stamped = act.set_last_run(record, "news")
        got = act.last_run(stamped, "news")
        ac3 = got == today
        detail3 = "last_run=" + repr(got) + ", local date is " + repr(today)
    except NameError as exc:
        ac3, detail3 = False, "raised NameError: " + str(exc)
    results.append(("AC 3: set_last_run(record, 'news') with no today", ac3, detail3))

    # --- AC 4 (mechanism half): ran_today is True after, and the answer
    #     fields survive the stamp. A second boot the same day must see this. ---
    if stamped is not None:
        after = act.ran_today(stamped, "news")
        preserved = (
            act.answered_at_version(stamped, "news") == "1.0.0"
            and act.is_active(stamped, "news") is True
        )
        ac4 = after is True and preserved
        detail4 = (
            "ran_today=" + str(after) + ", answer fields preserved=" + str(preserved)
        )
    else:
        ac4, detail4 = False, "set_last_run did not return a record"
    results.append(
        ("AC 4: same-day re-check sees the run, answer preserved", ac4, detail4)
    )

    # --- AC 5: the mutation check. Delete the import, require FAILURE. ---
    source = ACTIVATION_PY.read_text(encoding="utf-8")
    ac5 = False
    detail5 = "import line not found in activation.py"
    if IMPORT_LINE in source:
        tmp = REPO_ROOT / ".tmp" / "issue-20"
        tmp.mkdir(parents=True, exist_ok=True)
        mutant = tmp / "activation_without_datetime_import.py"
        mutant.write_text(source.replace(IMPORT_LINE, "", 1), encoding="utf-8")

        healthy = run_exercise(ACTIVATION_PY)
        mutated = run_exercise(mutant)

        ac5 = healthy.returncode == 0 and mutated.returncode != 0
        tail = (mutated.stderr.strip().splitlines() or ["<no stderr>"])[-1]
        detail5 = (
            "healthy exit="
            + str(healthy.returncode)
            + " ("
            + healthy.stdout.strip()
            + "), "
            + "mutated exit="
            + str(mutated.returncode)
            + " ("
            + tail
            + ")"
        )
        print("--- mutated run: datetime import deleted ---")
        print(mutated.stderr.rstrip() or "<no stderr>")
        print("--- end mutated run ---\n")
    results.append(
        ("AC 5: check fails when the datetime import is removed", ac5, detail5)
    )

    # --- Generalisation: no module uses a name it never defines. ---
    scanned = 0
    findings: list[tuple[Path, int, str]] = []
    for root in SCAN_ROOTS:
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            scanned += 1
            findings += [(path, ln, nm) for ln, nm in undefined_names(path)]
    sweep_detail = (
        str(scanned) + " files clean"
        if not findings
        else "; ".join(
            p.name + ":" + str(ln) + " " + repr(nm) for p, ln, nm in findings
        )
    )
    results.append(
        (
            "Sweep: no undefined name used at runtime in shipped Python",
            not findings,
            sweep_detail,
        )
    )

    for name, ok, detail in results:
        print("[" + ("PASS" if ok else "FAIL") + "] " + name + ": " + detail)

    passed = sum(1 for _, ok, _ in results if ok)
    print(
        "\n"
        + str(passed)
        + "/"
        + str(len(results))
        + " of this script's criteria pass."
    )
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
