#!/usr/bin/env python3
"""Issue #46 -- checks for the heartbeat's dream cycle.

Mechanism tier: drives `.claude/shared/dream_cycle.py` (state and the run gate) and
reads `.claude/shared/activation.py`, `update_brain.py`, and the heartbeat files
directly, against a scratch brain root under `C:/Projects/.tmp/second-brain-loop-46/`.
Never touches the live `.claude/activations.json` or the live store.

Criteria this script can prove by mechanism: 1, 2, 3, 4, 5, 6, 7, 8, 11.
Criteria that need a store (9, 10) are proved by `check_dream_cycle_store.py`.

Usage: python check_dream_cycle.py
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
# DREAM_CYCLE_SRC points the check at a mutant copy of `src` (see mutate.py).
SRC_ROOT = Path(os.environ.get("DREAM_CYCLE_SRC", REPO_ROOT / "src"))
SHARED = SRC_ROOT / ".claude" / "shared"
HEARTBEAT = SRC_ROOT / ".claude" / "skills" / "heartbeat"
UPDATE_BRAIN = SHARED / "update_brain.py"

SCRATCH_ROOT = Path("C:/Projects/.tmp/second-brain-loop-46")
SCRATCH_BRAIN = SCRATCH_ROOT / "brain"

sys.path.insert(0, str(SHARED))


def build_scratch_brain() -> Path:
    if SCRATCH_BRAIN.exists():
        shutil.rmtree(SCRATCH_BRAIN)
    (SCRATCH_BRAIN / ".claude").mkdir(parents=True)
    (SCRATCH_BRAIN / "CLAUDE.md").write_text("# scratch brain\n", encoding="utf-8")
    return SCRATCH_BRAIN


def main() -> int:
    results: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        results.append((name, bool(ok), detail))

    try:
        import activation as act
        import dream_cycle as dc
    except ImportError as e:
        for ac in (1, 2, 3, 4, 5, 7, 8, 11):
            check(f"AC{ac}", False, f"dream_cycle module missing: {e}")
        dc = None
        act = None

    if dc is not None:
        scratch = build_scratch_brain()
        path = scratch / ".claude" / "activations.json"
        rec = act.load_record(path)

        # AC 1: switch on/off, recorded in the activation record.
        rec = dc.switch(rec, "1.1.2", active=True)
        act.save_record(path, rec)
        on = dc.status(act.load_record(path))["active"]
        rec = dc.switch(act.load_record(path), "1.1.2", active=False)
        act.save_record(path, rec)
        off = dc.status(act.load_record(path))["active"]
        check(
            "AC1: switch on and off lands in the activation record",
            on is True and off is False,
            f"on={on} off={off}",
        )

        # AC 2: batch size stored; switching never loses it.
        rec = dc.set_batch_size(act.load_record(path), 40)
        rec = dc.switch(rec, "1.1.2", active=True)
        act.save_record(path, rec)
        bs = dc.status(act.load_record(path))["batch_size"]
        try:
            dc.set_batch_size({}, 0)
            rejects = False
        except ValueError:
            rejects = True
        check(
            "AC2: batch size is stored, survives a switch, 0 is refused",
            bs == 40 and rejects,
            f"batch_size={bs} rejects_zero={rejects}",
        )

        # AC 3: status reports on/off, batch size, cycles run, backlog.
        s = dc.status(act.load_record(path))
        check(
            "AC3: status carries active, batch_size, cycles_run, backlog",
            {"active", "batch_size", "cycles_run", "backlog"} <= set(s),
            f"keys={sorted(s)}",
        )

        # AC 11: switch, batch size and progress survive a fresh process.
        rec = dc.record_cycle(
            act.load_record(path),
            {"promoted": 3, "archived": 2, "retyped": 0},
            backlog_after=95,
        )
        act.save_record(path, rec)
        probe = (
            "import sys, json; sys.path.insert(0, %r); import activation as a, dream_cycle as d; "
            "print(json.dumps(d.status(a.load_record(a.Path(%r)))))"
            % (str(SHARED), str(path))
        )
        out = subprocess.run(
            [sys.executable, "-c", probe], capture_output=True, text=True
        )
        try:
            fresh = json.loads(out.stdout)
        except json.JSONDecodeError:
            fresh = {}
        check(
            "AC11a: state survives a fresh process",
            fresh.get("active") is True
            and fresh.get("batch_size") == 40
            and fresh.get("cycles_run") == 1
            and fresh.get("backlog") == 95,
            f"{fresh}",
        )

        # AC 4, 5, 7, 8: the gate's truth table.
        on_rec = dc.switch({}, "1.1.2", active=True)
        off_rec = dc.switch({}, "1.1.2", active=False)
        table = {
            "AC4: on + quiet + no curiosity + owner away runs": (
                dc.should_run(
                    on_rec, quiet=True, curiosity_ran=False, owner_active=False
                ),
                True,
            ),
            "AC5: off never runs": (
                dc.should_run(
                    off_rec, quiet=True, curiosity_ran=False, owner_active=False
                ),
                False,
            ),
            "AC7: never in the same beat as curiosity": (
                dc.should_run(
                    on_rec, quiet=True, curiosity_ran=True, owner_active=False
                ),
                False,
            ),
            "AC8: never while the owner is in conversation": (
                dc.should_run(
                    on_rec, quiet=True, curiosity_ran=False, owner_active=True
                ),
                False,
            ),
            "AC4b: not quiet does not run": (
                dc.should_run(
                    on_rec, quiet=False, curiosity_ran=False, owner_active=False
                ),
                False,
            ),
            "AC5b: no record at all does not run": (
                dc.should_run({}, quiet=True, curiosity_ran=False, owner_active=False),
                False,
            ),
        }
        for name, (got, want) in table.items():
            check(name, got is want, f"got={got} want={want}")

        # Design note (no criterion): the day's saved dry-run plan.
        acts = [
            {"action": "promote", "source_ids": ["a"]},
            {"action": "archive", "source_ids": ["b"]},
            {"action": "archive", "source_ids": ["c"]},
            {"action": "merge", "source_ids": ["d", "e"]},
            {"action": "flag_contradiction", "source_ids": ["f", "g"]},
        ]
        plan = dc.new_plan(acts, "2026-10-10")
        check(
            "PLAN: only reversible actions are planned, the rest are counted",
            len(plan["actions"]) == 3 and plan["needs_dream"] == 2,
            f"actions={len(plan['actions'])} needs_dream={plan['needs_dream']}",
        )
        batch = dc.next_batch(plan, 2)
        plan2 = dc.mark_applied(plan, [a["key"] for a in batch])
        batch2 = dc.next_batch(plan2, 2)
        check(
            "PLAN: a batch is capped and never re-takes an applied action",
            len(batch) == 2
            and [a["source_ids"][0] for a in batch2] == ["c"]
            and dc.backlog(plan2) == 1,
            f"batch={[a['key'] for a in batch]} next={[a['key'] for a in batch2]}",
        )
        used = dc.mark_applied(plan2, [a["key"] for a in batch2])
        check(
            "PLAN: stale on a new day or when used up, fresh otherwise",
            dc.plan_is_stale(plan, "2026-10-11")
            and dc.plan_is_stale(used, "2026-10-10")
            and dc.plan_is_stale(None, "2026-10-10")
            and not dc.plan_is_stale(plan2, "2026-10-10"),
        )
        ppath = scratch / ".claude" / dc.PLAN_FILE
        dc.save_plan(ppath, plan2)
        check(
            "PLAN: saved plan reloads identically",
            dc.load_plan(ppath) == plan2,
        )

    # AC 6: the heartbeat's own files name the dream cycle, paired by id.
    goal = (HEARTBEAT / "goal.md").read_text(encoding="utf-8")
    observe = (HEARTBEAT / "observe.md").read_text(encoding="utf-8")
    check(
        "AC6a: observe.md has the dream-cycle section by id",
        bool(re.search(r"id:\s*`?dream-cycle`?", observe)),
    )
    check(
        "AC6b: goal.md has the dream-cycle section by id",
        bool(re.search(r"id:\s*`?dream-cycle`?", goal)),
    )

    # AC 7 (text half): the rule is written in the heartbeat goal.
    check(
        "AC7b: heartbeat goal states curiosity and the dream cycle never share a beat",
        bool(re.search(r"never\s+both\s+in\s+the\s+same\s+beat", goal, re.I)),
    )

    # AC 5 and AC 8 (text half): the heartbeat goal says off means never, and the
    # 10-minute owner-in-conversation refusal, inside the dream-cycle section only.
    section = re.split(r"\n## ", goal)
    dream_section = next(
        (s for s in section if re.search(r"`?id:\s*dream-cycle`?", s)), ""
    )
    check(
        "AC6c: the dream-cycle goal section was found to be inspected",
        bool(dream_section),
    )
    check(
        "AC5c: dream-cycle goal section says off means never",
        bool(re.search(r"off\s+means\s+never", dream_section, re.I)),
    )
    check(
        "AC8b: dream-cycle goal section refuses while the owner is in conversation (10 minutes)",
        bool(re.search(r"owner[^.]*conversation", dream_section, re.I))
        and "10 minutes" in dream_section,
    )
    check(
        "AC4c: dream-cycle goal section runs one cycle per beat at the stored batch size",
        bool(re.search(r"one\s+cycle\s+per\s+beat", dream_section, re.I))
        and bool(re.search(r"batch\s+size", dream_section, re.I)),
    )

    # AC 11b: the record is carried across /update.
    ub = UPDATE_BRAIN.read_text(encoding="utf-8") if UPDATE_BRAIN.is_file() else ""
    check(
        "AC11b: update_brain.py treats activations.json as machine-local",
        ".claude/activations.json" in ub,
    )
    gi = (SRC_ROOT / ".gitignore").read_text(encoding="utf-8")
    check(
        "PLAN: the saved plan is machine-local and git-ignored",
        ".claude/dream-cycle-plan.json" in ub and ".claude/dream-cycle-plan.json" in gi,
    )

    width = max(len(n) for n, _, _ in results)
    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name.ljust(width)}  {detail}")
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n{passed}/{len(results)} checks pass")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
