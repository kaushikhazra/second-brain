"""Proof checks for #47: AC 1, 3, 4, 5, 6, 7. Exit 0 only if every check passes
AND every check is shown to fail when its behaviour is broken.

    python guard/check_guard.py

Each AC is a function over a hook folder / settings file / generator file, so the
same function can run on the shipped files and on a deliberately broken copy.
AC 2 is guard/test_unwrap.py; AC 8's numbers come from guard/train.py --eval.
"""

import json
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / "src" / ".claude" / "hooks"
SETTINGS = ROOT / "src" / ".claude" / "settings.json"
GUARD = ROOT / "guard"
SCRATCH = ROOT.parent / ".tmp"  # beside the repo, never the system temp folder
TIME_BOUND_S = 0.5  # median wall time of a fresh process per tool call


def call(hooks, tool, command):
    payload = json.dumps({"tool_name": tool, "tool_input": {"command": command}})
    t = time.perf_counter()
    out = subprocess.run(
        [sys.executable, str(hooks / "command_guard.py")],
        input=payload,
        capture_output=True,
        text=True,
        timeout=30,
    )
    dt = time.perf_counter() - t
    try:
        h = json.loads(out.stdout)["hookSpecificOutput"]
        return h["permissionDecision"], h.get("permissionDecisionReason", ""), dt
    except (ValueError, KeyError):
        return None, out.stdout + out.stderr, dt


# ------------------------------------------------------------------ checks
# each returns (ok, detail)


def ac1(settings, hooks):
    try:
        entries = json.loads(Path(settings).read_text(encoding="utf-8"))["hooks"][
            "PreToolUse"
        ]
    except (OSError, ValueError, KeyError):
        return False, "no PreToolUse hooks in settings"
    ours = [
        e
        for e in entries
        if any("command_guard.py" in h.get("command", "") for h in e.get("hooks", []))
        and all(
            re.search(rf"(^|\|){t}($|\|)", e.get("matcher", ""))
            for t in ("Bash", "PowerShell")
        )
    ]
    if not ours:
        return (
            False,
            "no matcher covering both Bash and PowerShell runs command_guard.py",
        )
    for tool in ("Bash", "PowerShell"):
        d, why, _ = call(hooks, tool, "git status")
        if d is None:
            return False, f"{tool}: hook gave no decision ({why[:80]})"
    d, _, _ = call(hooks, "Read", "git status")
    if d is not None:
        return False, "hook answered for a tool it does not guard"
    return True, "matcher covers Bash|PowerShell; both reach the hook"


def ac3(hooks):
    bad = [c for c in ("ls -la", "git status") if call(hooks, "Bash", c)[0] != "allow"]
    return not bad, "safe commands allow" if not bad else f"not allowed: {bad}"


def ac4(hooks):
    d, why, _ = call(hooks, "Bash", "rm -rf /var/www")
    ok = d == "deny" and "deletes" in why
    return ok, f"decision={d}, reason={why!r}"


def ac5(hooks):
    d, _, _ = call(hooks, "Bash", "pip install requests")
    return d == "ask", f"decision={d}"


def ac6(hooks):
    times = [call(hooks, "Bash", "git status")[2] for _ in range(20)]
    med = statistics.median(times)
    probe = (
        'import io,runpy,sys;sys.stdin=io.StringIO(\'{"tool_name":"Bash","tool_input":{"command":"ls"}}\');'
        f"\ntry: runpy.run_path(r'{hooks / 'command_guard.py'}',run_name='__main__')\nexcept SystemExit: pass\n"
        "print(sorted({m.split('.')[0] for m in sys.modules if not m.startswith('_')} - set(sys.stdlib_module_names) - {'sys'}))"
    )
    out = subprocess.run(
        [sys.executable, "-I", "-c", probe], capture_output=True, text=True
    ).stdout
    third = (
        [m for m in eval(out.strip().splitlines()[-1]) if m not in ("runpy", "io")]
        if out.strip()
        else ["?"]
    )
    ok = med <= TIME_BOUND_S and not third
    return (
        ok,
        f"median {med * 1000:.0f} ms (bound {TIME_BOUND_S * 1000:.0f}); non-stdlib imports: {third}",
    )


def ac7(generate, train, data):
    """Training reads no owner history: no reference to it in the code, no owner marker in the data."""
    markers = (
        "cmd-guard-dataset",
        "commands.jsonl",
        "scorecard",
        "history.jsonl",
        "transcript",
    )
    for f in (generate, train):
        text = Path(f).read_text(encoding="utf-8")
        hit = [m for m in markers if m in text]
        if hit:
            return False, f"{Path(f).name} refers to {hit}"
    blob = Path(data).read_text(encoding="utf-8", errors="replace")
    if re.search(r"hazra|Velasari|kaushik", blob, re.I):
        return False, "training data carries an owner name"
    return (
        True,
        "generator and trainer name no owner source; training data has no owner marker",
    )


# ------------------------------------------------------------------ break-it demos
# each builds a copy of the thing with the behaviour removed; the check must fail on it


def broken_hooks(scratch, **meta_change):
    d = scratch / f"hooks-{len(list(scratch.iterdir()))}"
    shutil.copytree(
        HOOKS, d, ignore=shutil.ignore_patterns("__pycache__", "memory_guard.py")
    )
    j = d / "command_guard.json"
    meta = json.loads(j.read_text(encoding="utf-8"))
    meta.update(meta_change)
    j.write_text(json.dumps(meta), encoding="utf-8")
    return d


def main():
    SCRATCH.mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="guard-check-", dir=SCRATCH))
    results = []

    def run(name, check, shipped, broken):
        ok, detail = check(*shipped)
        bad_ok, bad_detail = check(*broken)
        proven = ok and not bad_ok
        results.append(proven)
        print(f"{'PASS' if proven else 'FAIL'}  {name}: {detail}")
        print(
            f"      broken copy -> {'still passes (check is blind)' if bad_ok else 'fails: ' + bad_detail[:90]}"
        )

    try:
        # AC 1: settings without the entry
        s = work / "settings.json"
        s.write_text(
            json.dumps(
                {
                    "hooks": {
                        "PreToolUse": [
                            {
                                "matcher": "Bash",
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": "python command_guard.py",
                                    }
                                ],
                            }
                        ]
                    }
                }
            ),
            encoding="utf-8",
        )
        run("AC 1 both shells reach the guard", ac1, (SETTINGS, HOOKS), (s, HOOKS))
        # AC 3: a hook that never allows
        run(
            "AC 3 confident safe runs, no prompt",
            ac3,
            (HOOKS,),
            (broken_hooks(work, allow_below=-1.0),),
        )
        # AC 4: a hook that never denies
        run(
            "AC 4 confident risky is blocked, question named",
            ac4,
            (HOOKS,),
            (broken_hooks(work, deny_at=2.0),),
        )
        # AC 5: a hook with no ask band (everything denied)
        run(
            "AC 5 unsure stops and asks",
            ac5,
            (HOOKS,),
            (broken_hooks(work, deny_at=0.0),),
        )
        # AC 6: the bound itself, shown to bite
        global TIME_BOUND_S
        ok, detail = ac6(HOOKS)
        saved, TIME_BOUND_S = TIME_BOUND_S, 0.0
        bad_ok, _ = ac6(HOOKS)
        TIME_BOUND_S = saved
        results.append(ok and not bad_ok)
        print(
            f"{'PASS' if ok and not bad_ok else 'FAIL'}  AC 6 CPU only, no noticeable delay: {detail}"
        )
        print(
            f"      zero bound -> {'still passes (check is blind)' if bad_ok else 'fails as it should'}"
        )
        # AC 7: generator that reads an owner file; data with an owner name
        g = work / "generate.py"
        g.write_text(
            Path(GUARD / "generate.py").read_text(encoding="utf-8")
            + "\nopen('commands.jsonl')\n",
            encoding="utf-8",
        )
        d = work / "train.jsonl"
        d.write_text('{"command": "cat C:/Users/hazra/notes.md"}\n', encoding="utf-8")
        run(
            "AC 7 no owner history in training",
            ac7,
            (GUARD / "generate.py", GUARD / "train.py", GUARD / "data" / "train.jsonl"),
            (g, GUARD / "train.py", d),
        )
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print(f"\n{sum(results)} of {len(results)} checks hold and fail when broken")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
