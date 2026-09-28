#!/usr/bin/env python3
"""Issue #4 -- AC 1, AC 2, AC 9: the heartbeat's three files exist, their observe/goal
sections pair by id in both directions, and the folder makes no direct synaptra store
call.

AC 2 proof note (recorded in cycle-1's log, not re-run by this script every time):
copying observe.md with one extra `id:` line and re-running this script against the
copy makes AC 2 fail -- the pairing check is a real assertion, not a tautology.

Usage: python check_heartbeat.py [heartbeat-dir]
Defaults to the directory this file lives in.

Exit 0: all checks pass. Exit 1: one or more fail, printed by name.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ID_RE = re.compile(r"^`id:\s*([a-zA-Z0-9_-]+)`", re.MULTILINE)
FORBIDDEN_CALLS = ("memory_store", "memory_update", "memory_delete", "memory_archive")
CALL_RE = {call: re.compile(rf"\b{call}\s*\(") for call in FORBIDDEN_CALLS}


def find_ids(text: str) -> set[str]:
    return set(ID_RE.findall(text))


def main() -> int:
    heartbeat_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
    results: list[tuple[str, bool, str]] = []

    skill_file = heartbeat_dir / "SKILL.md"
    observe_file = heartbeat_dir / "observe.md"
    goal_file = heartbeat_dir / "goal.md"

    all_present = skill_file.is_file() and observe_file.is_file() and goal_file.is_file()
    results.append(
        (
            "AC1: SKILL.md, observe.md, goal.md all present",
            all_present,
            f"SKILL.md={skill_file.is_file()} observe.md={observe_file.is_file()} "
            f"goal.md={goal_file.is_file()}",
        )
    )

    if all_present:
        observe_text = observe_file.read_text(encoding="utf-8")
        goal_text = goal_file.read_text(encoding="utf-8")

        observe_ids = find_ids(observe_text)
        goal_ids = find_ids(goal_text)
        missing_in_goal = observe_ids - goal_ids
        missing_in_observe = goal_ids - observe_ids

        ok2 = bool(observe_ids) and not missing_in_goal and not missing_in_observe
        results.append(
            (
                "AC2: every section id pairs, both directions",
                ok2,
                f"observe={sorted(observe_ids)} goal={sorted(goal_ids)} "
                f"missing_in_goal={sorted(missing_in_goal)} "
                f"missing_in_observe={sorted(missing_in_observe)}",
            )
        )
    else:
        results.append(("AC2: every section id pairs, both directions", False, "skipped -- AC1 failed"))

    text_files = [
        p for p in heartbeat_dir.rglob("*")
        if p.is_file() and p.suffix in (".md", ".py")
    ]
    found_calls: list[str] = []
    for call, pattern in CALL_RE.items():
        for p in text_files:
            if p.name == "check_heartbeat.py":
                continue  # this script's own FORBIDDEN_CALLS/CALL_RE tables name the calls as data, not invocations
            if pattern.search(p.read_text(encoding="utf-8")):
                found_calls.append(f"{call} in {p.name}")
    ok3 = not found_calls
    results.append(
        (
            "AC9: no direct memory_store/update/delete/archive call in the heartbeat folder",
            ok3,
            "clean" if ok3 else f"found: {found_calls}",
        )
    )

    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")

    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n{passed}/{len(results)} of this script's criteria pass.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
