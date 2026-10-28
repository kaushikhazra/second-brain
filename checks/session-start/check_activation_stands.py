#!/usr/bin/env python3
"""Issue #95 proofs: an owner's activation answer stands until the habit itself changes.

Drives the real activation.py the way /session-start's activation step does, on the record
the issue reports (answers stamped 1.3.0, brain now at 1.7.0), and reads the skill for the
one thing only it can say: the re-ask carries a line on what changed.

    AC 1  a brain updated across releases that did not touch its habits is asked nothing
    AC 2  a habit changed after its answer is re-asked, and only that habit
    AC 3  the re-ask of a changed habit carries the note on what changed; a first ask does not
    AC 4  a habit never answered is asked
    AC 5  an answer whose version cannot be read is asked again
    AC 6  the skill tells the brain to put the change note in front of a changed habit's question

Each criterion is shown to bite: the same scenarios run on copies of the two files with one
behaviour removed, and the named criteria must FAIL.

    python checks/session-start/check_activation_stands.py
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC = REPO / "src"
SCRATCH_BASE = Path("C:/Projects/.tmp")
ACTIVATION = SRC / ".claude" / "shared" / "activation.py"
SKILL = SRC / ".claude" / "skills" / "session-start" / "SKILL.md"
HABITS = ["curiosity", "news"]
BRAIN_VERSION = "1.7.0"

# The record the issue reports, with the guard row left out (it is not asked at boot).
ISSUE_RECORD = {
    "curiosity": {"active": False, "answered_at_version": "1.3.0"},
    "news": {"active": False, "answered_at_version": "1.3.0"},
}

# One behaviour removed per mutant: (file, old, new, criteria that must fail).
MUTANTS = {
    "answers go stale on every release": (
        ACTIVATION,
        "    return answered < _version_key(changed_in(habit))",
        f'    return answered != _version_key("{BRAIN_VERSION}")',
        ("AC 1",),
    ),
    "a changed habit is never re-asked": (
        ACTIVATION,
        "    return answered < _version_key(changed_in(habit))",
        "    return False",
        ("AC 2", "AC 3"),
    ),
    "a never-answered habit is not asked": (
        ACTIVATION,
        "    if entry is None:\n        return True\n    answered",
        "    if entry is None:\n        return False\n    answered",
        ("AC 4",),
    ),
    "an unreadable answer stands": (
        ACTIVATION,
        "    if answered is None:\n        return True\n",
        "    if answered is None:\n        return False\n",
        ("AC 5",),
    ),
    "a first ask is flagged as a change": (
        ACTIVATION,
        "    return _entry(record, habit) is not None and needs_ask(record, habit)",
        "    return needs_ask(record, habit)",
        ("AC 3",),
    ),
    "skill drops the change note": (
        SKILL,
        "put `change_note(habit)` in front of the question",
        "ignore it",
        ("AC 6",),
    ),
}


def load(path: Path):
    spec = importlib.util.spec_from_file_location("activation", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def scenarios(act_py: Path, skill_text: str) -> dict[str, tuple[bool, str]]:
    r: dict[str, tuple[bool, str]] = {}
    act = load(act_py)

    asked = act.habits_to_ask(ISSUE_RECORD, HABITS, {})
    r["AC 1"] = (asked == [], f"asked {asked} on the issue's record at {BRAIN_VERSION}")

    act.HABIT_CHANGED_IN["news"] = ("1.8.0", "now lists local news too")
    asked = act.habits_to_ask(ISSUE_RECORD, HABITS, {})
    r["AC 2"] = (asked == ["news"], f"news changed in 1.8.0, asked {asked}")

    again = act.changed_since_answer(ISSUE_RECORD, "news")
    note = act.change_note("news")
    first = act.changed_since_answer({}, "news")
    r["AC 3"] = (
        again and note == "now lists local news too" and not first,
        f"changed_since_answer={again}, note={note!r}, first ask flagged as change={first}",
    )

    asked = act.habits_to_ask({}, HABITS, {})
    r["AC 4"] = (asked == HABITS, f"empty record, asked {asked}")

    junk = {"curiosity": {"active": True, "answered_at_version": "not-a-version"}}
    asked = act.habits_to_ask(junk, ["curiosity"], {})
    r["AC 5"] = (asked == ["curiosity"], f"unreadable answer version, asked {asked}")

    r["AC 6"] = (
        "put `change_note(habit)` in front of the question" in skill_text
        and "changed_since_answer" in skill_text,
        "skill names changed_since_answer and puts change_note in front of the question",
    )
    return r


def main() -> int:
    SCRATCH_BASE.mkdir(parents=True, exist_ok=True)
    base = SCRATCH_BASE / "sb-95-check"
    if base.exists():
        shutil.rmtree(base)
    base.mkdir()

    failed = 0
    print("== shipped files ==")
    real = scenarios(ACTIVATION, SKILL.read_text("utf-8"))
    for ac in sorted(real):
        ok, note = real[ac]
        print(f"  {'PASS' if ok else 'FAIL'}  {ac}  {note}")
        failed += not ok

    print("== each criterion bites ==")
    for i, (name, (target, old, new, must_fail)) in enumerate(MUTANTS.items()):
        text = target.read_text("utf-8")
        if old not in text:
            print(f"  FAIL  mutant '{name}': text to remove not found in {target.name}")
            failed += 1
            continue
        mutant = base / f"m{i}" / target.name
        mutant.parent.mkdir()
        mutant.write_text(text.replace(old, new, 1), encoding="utf-8", newline="")
        got = scenarios(
            mutant if target == ACTIVATION else ACTIVATION,
            mutant.read_text("utf-8") if target == SKILL else SKILL.read_text("utf-8"),
        )
        for ac in must_fail:
            bit = not got[ac][0]
            print(f"  {'PASS' if bit else 'FAIL'}  '{name}' makes {ac} fail")
            failed += not bit

    shutil.rmtree(base, ignore_errors=True)
    print("\nOK" if not failed else f"\n{failed} check(s) failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
