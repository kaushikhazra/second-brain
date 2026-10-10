#!/usr/bin/env python3
"""Issue #46 -- the owner's door and the cycle's bookkeeping, driven through the CLI.

Builds a scratch brain under `C:/Projects/.tmp/second-brain-loop-46/cli-brain/` holding
copies of `activation.py` and `dream_cycle.py`, then runs `dream_cycle.py` as the skill
does -- as a subprocess, one command at a time -- and reads the files it leaves. Never
touches the live brain or the live store; the memory calls themselves (retype, archive)
belong to `/update-memory` and `/delete-memory` and are proved by the skill-text checks
here and by the store run in a later cycle.

Proves: AC 1-3 (switch, size, status through the owner's commands), AC 4 (the skill
exists and runs one batch from the plan), AC 9 (a cycle logs what it did and the
backlog goes down), AC 10 (hand and heartbeat cycles count the same).

Usage: python check_dream_cycle_cli.py
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC = REPO_ROOT / "src"
SHARED = SRC / ".claude" / "shared"
SKILL = SRC / ".claude" / "skills" / "dream-cycle" / "SKILL.md"
SRC_CLAUDE_MD = SRC / "CLAUDE.md"

BRAIN = Path("C:/Projects/.tmp/second-brain-loop-46/cli-brain")


def build() -> Path:
    if BRAIN.exists():
        shutil.rmtree(BRAIN)
    shared = BRAIN / ".claude" / "shared"
    shared.mkdir(parents=True)
    (BRAIN / "CLAUDE.md").write_text("# scratch\n", encoding="utf-8")
    (BRAIN / "VERSION").write_text("9.9.9\n", encoding="utf-8")
    for name in ("activation.py", "dream_cycle.py"):
        shutil.copy(SHARED / name, shared / name)
    return shared / "dream_cycle.py"


def run(script: Path, *args: str) -> tuple[int, str]:
    r = subprocess.run(
        [sys.executable, str(script), *args], capture_output=True, text=True
    )
    return r.returncode, (r.stdout + r.stderr).strip()


def main() -> int:
    results: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        results.append((name, bool(ok), detail))

    script = build()
    record = BRAIN / ".claude" / "activations.json"
    plan_file = BRAIN / ".claude" / "dream-cycle-plan.json"
    log_file = BRAIN / ".claude" / "dream-cycle-log.md"

    # AC 1-3 through the owner's commands.
    _, out_on = run(script, "on")
    _, st_on = run(script, "status")
    _, out_off = run(script, "off")
    _, st_off = run(script, "status")
    check(
        "AC1: on and off say what resulted and status follows",
        "on" in out_on and "is on" in st_on and "off" in out_off and "is off" in st_off,
        f"{out_on!r} {st_on!r} {out_off!r} {st_off!r}",
    )
    rc_bad, out_bad = run(script, "size", "0")
    _, out_size = run(script, "size", "3")
    _, st = run(script, "status")
    check(
        "AC2: size is stored through the command, below 1 is refused and says so",
        rc_bad != 0
        and "Not changed" in out_bad
        and "Batch size is 3" in out_size
        and "Batch size 3" in st,
        f"{out_bad!r} {out_size!r}",
    )
    check(
        "AC3: status line names on/off, batch size, cycles run, backlog",
        all(w in st for w in ("Dream cycle is", "Batch size", "Cycles run", "Backlog")),
        st,
    )

    # A plan of 8 reversible actions and 2 that need a hand /dream.
    actions = (
        [
            {"action": "promote", "source_ids": [f"p{i}"], "to_type": "semantic"}
            for i in range(3)
        ]
        + [{"action": "archive", "source_ids": [f"a{i}"]} for i in range(5)]
        + [{"action": "merge", "source_ids": ["m1", "m2"]}]
        + [{"action": "flag_contradiction", "source_ids": ["c1", "c2"]}]
    )
    af = BRAIN / ".claude" / "actions.json"
    af.write_text(json.dumps(actions), encoding="utf-8")
    run(script, "off")
    _, out_plan = run(script, "plan-from", str(af))
    _, st_plan = run(script, "status")
    check(
        "AC9a: the plan counts what a cycle may apply and what needs a hand /dream",
        "8 to apply" in out_plan
        and "2 need a hand /dream" in out_plan
        and "Backlog 8" in st_plan,
        f"{out_plan!r} | {st_plan!r}",
    )

    # Two cycles, one by hand with the switch OFF, one from the heartbeat.
    _, b1 = run(script, "batch")
    batch1 = json.loads(b1)
    keys1 = ",".join(a["key"] for a in batch1)
    rc1, f1 = run(
        script,
        "finish",
        "--by",
        "hand",
        "--promoted",
        "2",
        "--archived",
        "0",
        "--skipped",
        "1",
        "--keys",
        keys1,
    )
    _, b2 = run(script, "batch")
    batch2 = json.loads(b2)
    keys2 = ",".join(a["key"] for a in batch2)
    rc2, f2 = run(
        script,
        "finish",
        "--by",
        "heartbeat",
        "--promoted",
        "0",
        "--archived",
        "3",
        "--skipped",
        "0",
        "--keys",
        keys2,
    )
    check(
        "AC4: a cycle takes at most the stored batch size, in plan order, never an applied action",
        len(batch1) == 3
        and len(batch2) == 3
        and not set(keys1.split(",")) & set(keys2.split(",")),
        f"batch1={keys1} batch2={keys2}",
    )
    lines = (
        log_file.read_text(encoding="utf-8").splitlines() if log_file.is_file() else []
    )
    shape = re.compile(
        r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2} by=(hand|heartbeat) promoted=\d+ archived=\d+ "
        r"skipped=\d+ backlog \d+->\d+$"
    )
    check(
        "AC9b: each cycle appends one log line saying what it did",
        len(lines) == 2 and all(shape.match(l) for l in lines),
        f"{lines}",
    )
    _, st_after = run(script, "status")
    check(
        "AC9c: the backlog count goes down (8 -> 5 -> 2)",
        "Backlog 2" in st_after
        and "backlog 8->5" in lines[0]
        and "backlog 5->2" in lines[1],
        f"{st_after!r}",
    )
    check(
        "AC10: hand and heartbeat cycles count the same (2 cycles run, same line shape)",
        "Cycles run 2" in st_after
        and len(
            {
                re.sub(
                    r"\d+",
                    "N",
                    l.split(" ", 2)[2]
                    .replace("by=hand", "by=X")
                    .replace("by=heartbeat", "by=X"),
                )
                for l in lines
            }
        )
        == 1
        and shape.match(lines[0]) is not None
        and shape.match(lines[1]) is not None
        and rc1 == 0
        and rc2 == 0,
        st_after,
    )

    # The plan is stale on a new day or when used up.
    _, b3 = run(script, "batch")
    run(
        script,
        "finish",
        "--by",
        "heartbeat",
        "--keys",
        ",".join(a["key"] for a in json.loads(b3)),
    )
    _, b4 = run(script, "batch")
    check("PLAN: a used-up plan is reported STALE", b4 == "STALE", b4)

    # The skill: exists, names its commands, and honours the rules.
    text = SKILL.read_text(encoding="utf-8") if SKILL.is_file() else ""
    check("AC4b: the dream-cycle skill exists", bool(text))
    check(
        "AC1b: the skill names on, off, size and status",
        all(
            c in text
            for c in (
                "/dream-cycle on",
                "/dream-cycle off",
                "/dream-cycle size",
                "/dream-cycle status",
            )
        ),
    )
    check(
        "AC8c: the skill refuses while the owner is in conversation",
        bool(re.search(r"owner is in conversation", text)) and "10 minutes" in text,
    )
    check(
        "Reversible: the skill routes through /update-memory and /delete-memory and forbids the direct write calls",
        "/update-memory" in text
        and "/delete-memory" in text
        and bool(re.search(r"never delete", text, re.I))
        and bool(
            re.search(
                r"Never call `memory_delete`, `memory_store` or `memory_update` directly",
                text,
            )
        ),
    )
    check(
        "No backup: the skill states there is no backup step",
        bool(re.search(r"no backup step", text, re.I)),
    )
    md = SRC_CLAUDE_MD.read_text(encoding="utf-8")
    check(
        "AC1c: src/CLAUDE.md routes the owner to /dream-cycle in both tables",
        md.count("dream-cycle") >= 2,
        f"mentions={md.count('dream-cycle')}",
    )

    width = max(len(n) for n, _, _ in results)
    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name.ljust(width)}  {detail}")
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n{passed}/{len(results)} checks pass")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
