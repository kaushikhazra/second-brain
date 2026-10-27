#!/usr/bin/env python3
"""Issue #75 proofs: both guards run on the brain's own Python, never the machine's.

Builds scratch brains under C:/Projects/.tmp/sb-75-* from a copy of src/ and runs the
REAL command from src/.claude/settings.json, through Git's bash, with a PATH that has
no python on it.

    AC 1  python off PATH: a memory_store the guard refuses is refused; a shell command
          the command guard blocks is blocked
    AC 2  neither hook command names `python` bare or an absolute path
    AC 3  the .venv interpreter is used; with no .venv, the standalone one under .python
    AC 4  after the brain folder is renamed, both guards still run
    AC 5  neither interpreter present: a message naming the guard, exit 1 (visible)
    AC 6  $CLAUDE_PROJECT_DIR expands in the settings command (run from another cwd)
    AC 7  the command guard answers through the launcher exactly as it does directly

Each criterion is shown to bite: the same scenarios run on copies of src/ with one
behaviour removed, and the named criteria must FAIL.

    python checks/guard/check_guards_own_python.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC = REPO / "src"
SCRATCH_BASE = Path("C:/Projects/.tmp")

MEMORY_CALL = {  # refused by AC 12: self-map is reserved
    "tool_name": "mcp__synaptra__memory_store",
    "tool_input": {"content": "x", "tags": ["self-map"]},
}
SHELL_CALL = {"tool_name": "Bash", "tool_input": {"command": "rm -rf /var/www"}}

# One behaviour removed per mutant: (file under src/, old, new, criteria that must fail).
MUTANTS = {
    "settings back on bare python": (
        ".claude/settings.json",
        'sh \\"$CLAUDE_PROJECT_DIR/.claude/hooks/run_guard.sh\\" memory_guard.py',
        'python \\"$CLAUDE_PROJECT_DIR/.claude/hooks/memory_guard.py\\"',
        ("AC 1", "AC 2"),
    ),
    "no standalone fallback": (
        ".claude/hooks/run_guard.sh",
        '    "$claude"/.python/*/python.exe \\\n    "$claude"/.python/*/bin/python3\n',
        '    "$claude/.venv/none"\n',
        ("AC 3",),
    ),
    "launcher resolves nothing relative to itself": (
        ".claude/hooks/run_guard.sh",
        'claude=$(dirname "$here")',
        'claude="C:/Projects/.tmp/sb-75-old-folder-name/.claude"',  # where the brain was
        ("AC 4",),
    ),
    "silent when no interpreter": (
        ".claude/hooks/run_guard.sh",
        "exit 1\n",
        "exit 0\n",
        ("AC 5",),
    ),
}


def git_bash() -> tuple[Path, str]:
    """Git's bash, and a PATH of its own tools only -- no python anywhere on it."""
    git = shutil.which("git")
    if not git:
        raise SystemExit("FAIL: git not on PATH, so no Git bash to run hooks with")
    # git.exe sits in cmd/ or mingw64/bin/ depending on the install; walk up to the root.
    root = next(
        (p for p in Path(git).resolve().parents if (p / "bin" / "bash.exe").is_file()),
        None,
    )
    if root is None:
        raise SystemExit(f"FAIL: no Git bash found above {git}")
    bash = root / "bin" / "bash.exe"
    path = f"{root / 'usr' / 'bin'};{root / 'bin'}"
    return bash, path


BASH, BARE_PATH = git_bash()


def build_venv(dest: Path) -> None:
    subprocess.run(
        [sys.executable, "-m", "venv", "--without-pip", str(dest)],
        check=True,
        capture_output=True,
    )


def make_brain(
    base: Path, name: str, venv: Path | None, standalone: bool, src: Path = SRC
) -> Path:
    brain = base / name
    shutil.copytree(src, brain, ignore=shutil.ignore_patterns("__pycache__", "skills"))
    claude = brain / ".claude"
    (claude / "activations.json").write_text(
        json.dumps({"guard": {"active": True}}), encoding="utf-8"
    )
    if venv:
        shutil.copytree(venv, claude / ".venv")
    if standalone and venv:
        # python.exe + pyvenv.cfg side by side is a working interpreter with no .venv.
        slot = claude / ".python" / "cpython-3.12-test"
        slot.mkdir(parents=True)
        shutil.copy(venv / "Scripts" / "python.exe", slot / "python.exe")
        shutil.copy(venv / "pyvenv.cfg", slot / "pyvenv.cfg")
    return brain


def hook_commands(brain: Path) -> dict[str, str]:
    """matcher-group name -> the command, straight from the brain's settings.json."""
    settings = json.loads((brain / ".claude" / "settings.json").read_text("utf-8"))
    out = {}
    for group in settings["hooks"]["PreToolUse"]:
        for h in group["hooks"]:
            name = "memory" if "memory" in group["matcher"] else "command"
            out[name] = h["command"]
    return out


def fire(brain: Path, which: str, call: dict, cwd: Path) -> subprocess.CompletedProcess:
    """Run the settings.json command the way Claude Code does: bash -c, project dir in env."""
    command = hook_commands(brain)[which]
    return subprocess.run(
        [str(BASH), "-c", command],
        input=json.dumps(call),
        cwd=cwd,
        env={"PATH": BARE_PATH, "CLAUDE_PROJECT_DIR": brain.as_posix()},
        capture_output=True,
        text=True,
        timeout=60,
        encoding="utf-8",
        errors="replace",
    )


def is_deny(r: subprocess.CompletedProcess, which: str) -> bool:
    if which == "memory":
        return r.returncode == 2 and "self-map" in r.stderr
    try:
        out = json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"]
    except (ValueError, KeyError):
        return False
    return r.returncode == 0 and out == "deny"


def both_guard(brain: Path, cwd: Path) -> tuple[bool, str]:
    m = fire(brain, "memory", MEMORY_CALL, cwd)
    c = fire(brain, "command", SHELL_CALL, cwd)
    ok = is_deny(m, "memory") and is_deny(c, "command")
    return (
        ok,
        f"memory exit {m.returncode} {m.stderr.strip()[:80]!r}; command exit {c.returncode} {c.stdout.strip()[:60]!r} {c.stderr.strip()[:80]!r}",
    )


def scenarios(src: Path, base: Path, venv: Path) -> dict[str, tuple[bool, str]]:
    results: dict[str, tuple[bool, str]] = {}
    elsewhere = base / "elsewhere"
    elsewhere.mkdir(exist_ok=True)

    a = make_brain(base, "a", venv, standalone=False, src=src)
    results["AC 1"] = both_guard(a, elsewhere)
    results["AC 6"] = results["AC 1"]  # same run: expansion happens or nothing is found

    cmds = hook_commands(a)
    bare = [
        k
        for k, v in cmds.items()
        if v.lstrip().startswith("python") or ":/" in v or ":\\" in v
    ]
    results["AC 2"] = (not bare, f"offenders: {bare or 'none'}; commands {cmds}")

    only_venv = both_guard(a, elsewhere)
    b = make_brain(base, "b", venv, standalone=True, src=src)
    shutil.rmtree(b / ".claude" / ".venv")
    only_standalone = both_guard(b, elsewhere)
    results["AC 3"] = (
        only_venv[0] and only_standalone[0],
        f"venv: {only_venv[1]} | standalone: {only_standalone[1]}",
    )

    c = make_brain(base, "c", venv, standalone=False, src=src)
    moved = base / "renamed-brain"
    c.rename(moved)
    results["AC 4"] = both_guard(moved, elsewhere)

    d = make_brain(base, "d", None, standalone=False, src=src)
    m = fire(d, "memory", MEMORY_CALL, elsewhere)
    k = fire(d, "command", SHELL_CALL, elsewhere)
    results["AC 5"] = (
        m.returncode == 1
        and k.returncode == 1
        and "memory_guard.py" in m.stderr
        and "command_guard.py" in k.stderr,
        f"memory exit {m.returncode} {m.stderr.strip()[:90]!r}; command exit {k.returncode}",
    )

    direct = subprocess.run(
        [
            str(a / ".claude" / ".venv" / "Scripts" / "python.exe"),
            str(a / ".claude" / "hooks" / "command_guard.py"),
        ],
        input=json.dumps(SHELL_CALL),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    via = fire(a, "command", SHELL_CALL, elsewhere)
    results["AC 7"] = (
        direct.returncode == via.returncode
        and direct.stdout == via.stdout
        and bool(via.stdout),
        f"direct exit {direct.returncode}, launcher exit {via.returncode}, same stdout {direct.stdout == via.stdout}",
    )
    return results


def main() -> int:
    SCRATCH_BASE.mkdir(parents=True, exist_ok=True)
    base = SCRATCH_BASE / "sb-75-check"
    if base.exists():
        shutil.rmtree(base)
    base.mkdir()
    venv = base / "venv-template"
    build_venv(venv)

    failed = 0
    print("== shipped src/ ==")
    (base / "real").mkdir()
    real = scenarios(SRC, base / "real", venv)
    for ac in sorted(real):
        ok, note = real[ac]
        print(f"  {'PASS' if ok else 'FAIL'}  {ac}  {note}")
        failed += not ok

    print("== each criterion bites ==")
    for name, (rel, old, new, must_fail) in MUTANTS.items():
        mutant_src = base / f"mutant-{abs(hash(name))}"
        shutil.copytree(
            SRC, mutant_src, ignore=shutil.ignore_patterns("__pycache__", "skills")
        )
        target = mutant_src / rel
        text = target.read_text("utf-8")
        if old not in text:
            print(f"  FAIL  mutant '{name}': text to remove not found in {rel}")
            failed += 1
            continue
        target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="")
        work = base / f"m-{abs(hash(name))}"
        work.mkdir()
        got = scenarios(mutant_src, work, venv)
        for ac in must_fail:
            bit = not got[ac][0]
            print(f"  {'PASS' if bit else 'FAIL'}  '{name}' makes {ac} fail")
            failed += not bit

    shutil.rmtree(base, ignore_errors=True)
    print("\nOK" if not failed else f"\n{failed} check(s) failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
