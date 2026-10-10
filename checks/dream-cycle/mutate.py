#!/usr/bin/env python3
"""Issue #46 -- mutation pass: does each check fail when its behaviour is removed?

For each criterion, copy `src` to a scratch dir, remove ONE behaviour from the copy, run
the check that is meant to prove that criterion against the copy (`DREAM_CYCLE_SRC`), and
see whether a check line for THAT criterion fails. A mutation is

  KILLED         a `[FAIL] AC<n>...` line appeared: the check proves the criterion.
  SURVIVED       no line for that criterion failed: the check does not prove it.
  NOT_APPLIED    the text to remove was not found (the mutation, not the check, is broken).

A baseline run of the unmutated copy must be green first, or the pass means nothing.
Scratch copies live under `C:/Projects/.tmp/second-brain-loop-46/mutants/` and are removed.

AC 9 is mutation-proven separately by `check_dream_cycle_store.py` (apply calls removed,
cycle 5): it needs a real store, so it is not repeated here.

Usage: python mutate.py            exit 0 only if every mutation is KILLED
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
SRC = REPO_ROOT / "src"
MUTANTS = Path("C:/Projects/.tmp/second-brain-loop-46/mutants")

CORE = HERE / "check_dream_cycle.py"
CLI = HERE / "check_dream_cycle_cli.py"

DC = ".claude/shared/dream_cycle.py"

# (criterion, what is removed, file under src, text to find, replacement, check script)
MUTATIONS: list[tuple[str, str, str, str, str, Path]] = [
    (
        "1",
        "the switch ignores off",
        DC,
        '        "active": bool(active),\n',
        '        "active": True,\n',
        CORE,
    ),
    (
        "2",
        "the batch size is not stored",
        DC,
        '        "batch_size": n,\n',
        '        "batch_size": 25,\n',
        CORE,
    ),
    (
        "3",
        "status drops cycles_run",
        DC,
        '        "cycles_run": int(e.get("cycles_run", 0)),\n',
        '        "cycles": int(e.get("cycles_run", 0)),\n',
        CORE,
    ),
    (
        "4",
        "a cycle ignores the batch size",
        DC,
        "    return pending(plan)[: max(0, int(n))]",
        "    return pending(plan)",
        CLI,
    ),
    (
        "5",
        "the gate ignores the switch",
        DC,
        '        bool(_entry(record).get("active", False))\n',
        "        True\n",
        CORE,
    ),
    (
        "6",
        "the heartbeat does not name the dream cycle",
        ".claude/skills/heartbeat/observe.md",
        "id: dream-cycle",
        "id: no-such-section",
        CORE,
    ),
    (
        "7",
        "the gate lets curiosity and the cycle share a beat",
        DC,
        "        and not curiosity_ran\n",
        "",
        CORE,
    ),
    (
        "8",
        "the gate ignores the owner being in conversation",
        DC,
        "        and not owner_active\n",
        "",
        CORE,
    ),
    (
        "10",
        "a hand cycle is logged in a different shape",
        DC,
        '        f"backlog {backlog_before}->{backlog_after}"\n    )',
        '        f"backlog {backlog_before}->{backlog_after}"\n'
        '        + (" (hand)" if by == "hand" else "")\n    )',
        CLI,
    ),
    (
        "11",
        "/update would not carry the record across",
        ".claude/shared/update_brain.py",
        '        ".claude/activations.json",\n',
        "",
        CORE,
    ),
    (
        "11",
        "a restart loses the record",
        ".claude/shared/activation.py",
        "    return data if isinstance(data, dict) else {}",
        "    return {}",
        CORE,
    ),
]


def run_check(script: Path, src: Path) -> tuple[int, str]:
    env = {**os.environ, "DREAM_CYCLE_SRC": str(src)}
    r = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True, env=env
    )
    return r.returncode, r.stdout + r.stderr


def main() -> int:
    if MUTANTS.exists():
        shutil.rmtree(MUTANTS)
    MUTANTS.mkdir(parents=True)
    survivors = 0

    base = MUTANTS / "baseline"
    shutil.copytree(SRC, base)
    for script in (CORE, CLI):
        rc, out = run_check(script, base)
        if rc != 0:
            print(
                f"BASELINE RED for {script.name}: the pass means nothing until it is green."
            )
            print(out)
            shutil.rmtree(MUTANTS)
            return 2
    print("baseline green: both checks pass on an unmutated copy\n")

    for n, (ac, what, rel, old, new, script) in enumerate(MUTATIONS, 1):
        dest = MUTANTS / f"m{n}-ac{ac}"
        shutil.copytree(SRC, dest)
        target = dest / rel
        text = target.read_text(encoding="utf-8")
        if text.count(old) < 1:
            print(f"NOT_APPLIED  AC {ac:>2}  {what}  ({rel}: text not found)")
            survivors += 1
            continue
        target.write_text(text.replace(old, new, 1), encoding="utf-8")
        rc, out = run_check(script, dest)
        hit = re.findall(rf"^\[FAIL\] (AC{ac}(?!\d)\S*)", out, re.M)
        other = re.findall(r"^\[FAIL\] (\S+)", out, re.M)
        if hit:
            print(f"KILLED       AC {ac:>2}  {what}  <- {', '.join(hit)}")
        else:
            survivors += 1
            print(
                f"SURVIVED     AC {ac:>2}  {what}  (rc={rc}, other failures: {other or 'none'})"
            )

    shutil.rmtree(MUTANTS)
    print(f"\n{len(MUTATIONS) - survivors}/{len(MUTATIONS)} mutations killed")
    return 0 if survivors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
