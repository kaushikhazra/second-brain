#!/usr/bin/env python3
"""Issue #61 proofs: the owner switches the command guard off and back on.

Builds scratch brains under C:/Projects/.tmp/sb-61-* from a copy of src/ and drives
the real hook, the real /guard script and the real updater against them.

    AC 1  /guard off and /guard on switch the guard, through the activation record
    AC 2  the choice persists across processes and survives /update
    AC 3  off: no command is blocked, asked about or acknowledged -- model and
          plain checks alike (plain, -c wrapper, base64 payload, PowerShell)
    AC 4  each session start prints one line when the guard is off
    AC 5  a new brain starts with the guard off
    AC 6  an updated brain that had the guard keeps it on

Each criterion is shown to bite: the same scenarios run on copies of src/ with one
behaviour removed, and the named criteria must FAIL.

    python checks/guard/check_guard_switch.py
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC = REPO / "src"
SCRATCH_BASE = Path("C:/Projects/.tmp")

CALLS = {  # a command the guard denies when on, in each form the guard reads
    "plain": ("Bash", "rm -rf /var/www"),
    "-c wrapper": ("Bash", 'bash -c "rm -rf /var/www"'),
    "base64": ("Bash", "echo cm0gLXJmIC92YXIvd3d3 | base64 -d | sh"),
    "powershell": ("PowerShell", r"Remove-Item -Recurse -Force C:\inetpub\wwwroot"),
}
OFF_LINE_MARK = "command guard is off"
GUARD_SCRIPT = ".claude/skills/guard/scripts/guard.py"

# One behaviour removed per mutant: (file under src/, old, new, criteria that must fail).
MUTANTS = {
    "hook ignores the switch": (
        ".claude/hooks/command_guard.py",
        "    if not switched_on():\n",
        "    if False:\n",
        ("AC 1", "AC 3", "AC 5"),
    ),
    "hook defaults to on": (
        ".claude/hooks/command_guard.py",
        "except (OSError, ValueError, KeyError, TypeError):\n        return False",
        "except (OSError, ValueError, KeyError, TypeError):\n        return True",
        ("AC 5",),
    ),
    "/guard writes nothing": (
        ".claude/skills/guard/scripts/guard.py",
        "        save_record(record_path(ROOT), record)\n",
        "        pass\n",
        ("AC 1",),
    ),
    "no off line": (
        ".claude/skills/guard/scripts/guard.py",
        "            print(OFF_LINE)\n",
        "            pass\n",
        ("AC 4",),
    ),
    "session-start skips the line": (
        ".claude/skills/session-start/SKILL.md",
        "guard.py line",
        "guard.py status",
        ("AC 4",),
    ),
    "update forgets the guard": (
        ".claude/shared/update_brain.py",
        "        keep_guard_setting(brain, had_guard, brain_version, backup_dir)\n",
        "",
        ("AC 6",),
    ),
    "update overwrites the owner's choice": (
        ".claude/shared/update_brain.py",
        'or "guard" in record:',
        ":",
        ("AC 2",),
    ),
}


def run(args, cwd=None, stdin=None):
    return subprocess.run(
        [sys.executable, *map(str, args)],
        cwd=cwd,
        input=stdin,
        capture_output=True,
        text=True,
        timeout=120,
        encoding="utf-8",
        errors="replace",
    )


def hook(brain: Path, tool: str, command: str) -> str:
    payload = json.dumps({"tool_name": tool, "tool_input": {"command": command}})
    r = run([brain / ".claude" / "hooks" / "command_guard.py"], stdin=payload)
    return (
        r.stdout.strip() if r.returncode == 0 else f"ERROR {r.returncode}: {r.stderr}"
    )


def decision(out: str) -> str:
    """'' (silent), 'deny', or the raw output when it is neither."""
    if not out:
        return ""
    try:
        return json.loads(out)["hookSpecificOutput"]["permissionDecision"]
    except (ValueError, KeyError):
        return out


def verdicts(brain: Path, ack: bool = False) -> dict[str, str]:
    out = {}
    for name, (tool, command) in CALLS.items():
        first = hook(brain, tool, command)
        got = decision(first)
        if ack and got == "deny":
            code = re.search(r"guard-ack:([0-9a-f]+)", first).group(1)
            got = decision(hook(brain, tool, f"{command} # guard-ack:{code}"))
        out[name] = got
    return out


def guard(brain: Path, action: str) -> str:
    r = run([brain / GUARD_SCRIPT, action], cwd=brain)
    return (r.stdout + r.stderr).strip()


def entry(brain: Path):
    path = brain / ".claude" / "activations.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8")).get("guard")


def new_brain(tree: Path, where: Path) -> Path:
    if where.exists():
        shutil.rmtree(where)
    shutil.copytree(tree, where, ignore=shutil.ignore_patterns("__pycache__"))
    return where


def update(brain: Path, tree: Path) -> subprocess.CompletedProcess:
    return run(
        [
            tree / ".claude" / "shared" / "update_brain.py",
            brain,
            "--release",
            tree,
            "--skip-synaptra",
        ]
    )


def session_start_line(brain: Path) -> list[str]:
    """Run the command /session-start's report step tells the brain to run."""
    text = (brain / ".claude" / "skills" / "session-start" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    m = re.search(
        r"```bash\n(python \.claude/skills/guard/scripts/guard\.py \w+)\n```", text
    )
    if not m:
        return ["<no guard command in session-start SKILL.md>"]
    args = m.group(1).split()[1:]
    r = run(args, cwd=brain)
    return [ln for ln in r.stdout.splitlines() if ln.strip()]


def criteria(tree: Path, work: Path) -> dict[str, tuple[bool, str]]:
    res: dict[str, tuple[bool, str]] = {}
    root = work / "brain"

    # AC 5 -- a new brain: the tree as shipped, no activation record at all
    b = new_brain(tree, root)
    shipped_record = (b / ".claude" / "activations.json").exists()
    v_new = verdicts(b)
    line_new = guard(b, "line")
    res["AC 5"] = (
        not shipped_record
        and all(v == "" for v in v_new.values())
        and OFF_LINE_MARK in line_new,
        f"record shipped={shipped_record}, verdicts={v_new}, line={line_new!r}",
    )

    # AC 1 -- /guard on then off then on, judged by what the hook does
    guard(b, "on")
    on_entry, v_on = entry(b), verdicts(b)
    guard(b, "off")
    off_entry, v_off = entry(b), verdicts(b)
    guard(b, "on")
    back_entry, v_back = entry(b), verdicts(b)
    control = v_on["plain"] == "deny" and v_on["-c wrapper"] == "deny"
    skill = (b / ".claude" / "skills" / "guard" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    claude = (b / "CLAUDE.md").read_text(encoding="utf-8")
    shape = {"answered_at_version", "active"}
    res["AC 1"] = (
        control
        and (on_entry or {}).get("active") is True
        and (off_entry or {}).get("active") is False
        and (back_entry or {}).get("active") is True
        and set(off_entry or {}) == shape
        and all(v == "" for v in v_off.values())
        and v_back == v_on
        and "/guard off" in skill
        and "/guard on" in skill
        and "`/guard`" in claude,
        f"control(on denies plain+wrapper)={control}, on={on_entry}, off={off_entry}, "
        f"off verdicts={v_off}",
    )

    # AC 3 -- off means silent for every form, with the ack, and without weights
    guard(b, "off")
    v_off = verdicts(b)
    v_ack = verdicts(b, ack=True)
    (b / ".claude" / "hooks" / "command_guard.bin").unlink()
    v_noweights = verdicts(b)
    res["AC 3"] = (
        control
        and all(
            v == "" for v in (*v_off.values(), *v_ack.values(), *v_noweights.values())
        ),
        f"off={v_off}, acked={v_ack}, no weights={v_noweights}",
    )

    # AC 4 -- the line /session-start prints: one when off, none when on
    b = new_brain(tree, root)
    guard(b, "off")
    lines_off = session_start_line(b)
    guard(b, "on")
    lines_on = session_start_line(b)
    res["AC 4"] = (
        len(lines_off) == 1 and OFF_LINE_MARK in lines_off[0] and lines_on == [],
        f"off prints {lines_off}, on prints {lines_on}",
    )

    # AC 2 -- the choice outlives the process and /update, either way round
    kept = {}
    for choice in ("off", "on"):
        b = new_brain(tree, root)
        guard(b, choice)
        before = entry(b)
        r = update(b, tree)
        after = entry(b)
        again = [decision(hook(b, *CALLS["plain"]))]
        want = "" if choice == "off" else "deny"
        kept[choice] = r.returncode == 0 and after == before and again == [want]
    res["AC 2"] = (
        all(kept.values()),
        f"survives update: off kept={kept['off']}, on kept={kept['on']}",
    )

    # AC 6 -- an updated brain that had the guard (no record yet) has it on afterwards
    b = new_brain(tree, root)
    had = (b / ".claude" / "hooks" / "command_guard.py").is_file()
    r = update(b, tree)
    v_upd = verdicts(b)
    # boundary, not a criterion: a brain that never had the guard is not given one
    b2 = new_brain(tree, work / "brain-without-guard")
    (b2 / ".claude" / "hooks" / "command_guard.py").unlink()
    update(b2, tree)
    res["AC 6"] = (
        had
        and r.returncode == 0
        and (entry(b) or {}).get("active") is True
        and v_upd["plain"] == "deny"
        and v_upd["-c wrapper"] == "deny"
        and entry(b2) is None,
        f"had guard={had}, exit {r.returncode}, entry={entry(b)}, verdicts={v_upd}, "
        f"brain without the guard gets entry={entry(b2)}",
    )
    return res


def main() -> int:
    base = SCRATCH_BASE / "sb-61-switch"
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)

    print("=== shipped src/ ===")
    real = criteria(SRC, base / "real")
    for name in sorted(real):
        ok, detail = real[name]
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail[:230]}")
    held = sum(ok for ok, _ in real.values())
    print(f"\n{held}/{len(real)} criteria hold.")

    bite_ok = True
    for label, (rel, old, new, must_fail) in MUTANTS.items():
        tree = new_brain(SRC, base / "mutants" / re.sub(r"\W+", "-", label))
        target = tree / rel
        text = target.read_text(encoding="utf-8")
        if old not in text:
            raise SystemExit(f"FAIL: mutant '{label}' does not apply to {rel}")
        target.write_text(text.replace(old, new, 1), encoding="utf-8")
        got = criteria(tree, base / "mutants" / "work")
        bad = [m for m in must_fail if got[m][0]]
        bite_ok = bite_ok and not bad
        shown = ", ".join(
            f"{m} {'DID NOT FAIL' if m in bad else 'fails'}" for m in must_fail
        )
        print(f"broken copy [{label}]: {shown}")
    print(f"\nEvery criterion bites: {bite_ok}")
    shutil.rmtree(base, ignore_errors=True)
    return 0 if held == len(real) and bite_ok else 1


if __name__ == "__main__":
    sys.exit(main())
