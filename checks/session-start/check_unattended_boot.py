#!/usr/bin/env python3
"""Issue #81 proofs: an unattended boot never waits at an activation question.

Drives the real activation.py the way /session-start's activation step does (the import line
is taken from the skill's own text and executed, so a name the skill uses but the module lacks
fails here), and reads the skill and brain.bat for what only they can say.

    AC 1  SECOND_BRAIN_UNATTENDED set: no question is put, nothing is written to the record
    AC 2  on that boot every habit with no answer stays off
    AC 3  the next attended boot, same VERSION, asks each habit with no answer
    AC 4  a habit already answered at this VERSION is not asked on an attended boot
    AC 5  empty, 0, false, no mean attended; anything else means unattended
    AC 6  the skill tells the owner, in one line, that the questions were skipped
    AC 7  brain.bat's header names the variable and says what it does

Each criterion is shown to bite: the same scenarios run on copies of the three files with one
behaviour removed, and the named criteria must FAIL.

    python checks/session-start/check_unattended_boot.py
"""

from __future__ import annotations

import importlib.util
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC = REPO / "src"
SCRATCH_BASE = Path("C:/Projects/.tmp")
ACTIVATION = SRC / ".claude" / "shared" / "activation.py"
SKILL = SRC / ".claude" / "skills" / "session-start" / "SKILL.md"
BRAIN_BAT = SRC / "brain.bat"
ENV = "SECOND_BRAIN_UNATTENDED"
VERSION = "1.6.2"
SKIPPED_LINE = "Unattended boot — activation questions skipped"

# One behaviour removed per mutant: (file, old, new, criteria that must fail).
MUTANTS = {
    "unattended boot still asks": (
        ACTIVATION,
        "    if unattended(env):\n        return []\n",
        "",
        ("AC 1", "AC 2"),
    ),
    "0 / false / no count as unattended": (
        ACTIVATION,
        '("", "0", "false", "no")',
        '("",)',
        ("AC 5",),
    ),
    "answered habits are asked again": (
        ACTIVATION,
        "if needs_ask(record, h, version)",
        "if True",
        ("AC 4",),
    ),
    "skill no longer imports the new names": (
        SKILL,
        "habits_to_ask, unattended, set_answer",
        "needs_ask, set_answer",
        ("AC 1",),
    ),
    "skill is silent about the skip": (
        SKILL,
        SKIPPED_LINE,
        "Booting",
        ("AC 6",),
    ),
    "brain.bat does not name the variable": (
        BRAIN_BAT,
        "SECOND_BRAIN_UNATTENDED",
        "SECOND_BRAIN_X",
        ("AC 7",),
    ),
}


def load(path: Path):
    spec = importlib.util.spec_from_file_location("activation", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def habit_keys(skill_text: str) -> list[str]:
    return re.findall(r"^\| `(\w+)` \| \"", skill_text, re.M)


def boot(act, record: dict, habits: list[str], env: dict) -> tuple[list[str], dict]:
    """A boot where nobody answers: whatever is asked is recorded as declined, as the
    skill says of a question left unanswered. Returns (asked, record after)."""
    asked = act.habits_to_ask(record, habits, VERSION, env)
    for h in asked:
        record = act.set_answer(record, h, VERSION, active=False)
    return asked, record


def scenarios(
    act_py: Path, skill_text: str, bat_text: str
) -> dict[str, tuple[bool, str]]:
    r: dict[str, tuple[bool, str]] = {}
    act = load(act_py)
    habits = habit_keys(skill_text)

    # The skill's import line must name only things the module has.
    line = next(
        (l for l in skill_text.splitlines() if l.startswith("from activation import")),
        "",
    )
    names = [
        n.strip()
        for n in line.removeprefix("from activation import").split(",")
        if n.strip()
    ]
    missing = [n for n in names if not hasattr(act, n)]
    uses = {"habits_to_ask", "unattended"} <= set(names)

    asked, after = boot(act, {}, habits, {ENV: "1"})
    r["AC 1"] = (
        asked == [] and after == {} and not missing and uses and bool(habits),
        f"asked={asked}, record={after}, skill imports habits_to_ask+unattended={uses}, "
        f"names the module lacks={missing}",
    )
    r["AC 2"] = (
        all(not act.is_active(after, h) for h in habits) and after == {},
        f"active after unattended boot: {[h for h in habits if act.is_active(after, h)]}",
    )

    asked_later, _ = boot(act, after, habits, {})
    r["AC 3"] = (
        sorted(asked_later) == sorted(habits) and bool(habits),
        f"attended boot after it asks {asked_later} of {habits}",
    )

    answered = act.set_answer({}, habits[0], VERSION, active=True) if habits else {}
    asked_att = act.habits_to_ask(answered, habits, VERSION, {})
    r["AC 4"] = (
        bool(habits)
        and habits[0] not in asked_att
        and sorted(asked_att) == sorted(habits[1:]),
        f"answered {habits[:1]}, then asked {asked_att}",
    )

    attended = ["", "0", "false", "no", "NO", " "]
    unatt = ["1", "true", "yes", "on", "anything"]
    bad = [v for v in attended if act.unattended({ENV: v})] + [
        v for v in unatt if not act.unattended({ENV: v})
    ]
    r["AC 5"] = (not bad and not act.unattended({}), f"misread values: {bad}")

    r["AC 6"] = (
        SKIPPED_LINE in skill_text,
        f"skill carries {SKIPPED_LINE!r}: {SKIPPED_LINE in skill_text}",
    )

    head = "\n".join(
        l for l in bat_text.splitlines()[:20] if l.upper().startswith("REM")
    )
    r["AC 7"] = (
        ENV in head and "ask" in head.lower(),
        f"header names {ENV}: {ENV in head}",
    )
    return r


def main() -> int:
    SCRATCH_BASE.mkdir(parents=True, exist_ok=True)
    base = SCRATCH_BASE / "sb-81-check"
    if base.exists():
        shutil.rmtree(base)
    base.mkdir()

    failed = 0
    print("== shipped files ==")
    real = scenarios(ACTIVATION, SKILL.read_text("utf-8"), BRAIN_BAT.read_text("utf-8"))
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
            mutant.read_text("utf-8")
            if target == BRAIN_BAT
            else BRAIN_BAT.read_text("utf-8"),
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
