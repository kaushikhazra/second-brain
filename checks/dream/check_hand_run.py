#!/usr/bin/env python3
"""Issue #85 proofs: a consolidation the owner runs by hand is not refused for the owner having
just spoken; an automatic one still is.

The artifact is skill text, so the check reads the two skills for what each must say, section by
section, and shows each criterion bites by removing the sentence that carries it.

    AC 1  /dream: a bare /dream, typed by the owner, skips the active-conversation check
    AC 2  /dream: an invocation carrying "requested by <requester>" is refused within 10 minutes
          of an owner message, and the refusal says why
    AC 3  /dream: the 10-minute window is unchanged
    AC 4  /dream-cycle: a bare /dream-cycle, typed by the owner, is not stopped by it
    AC 5  /dream-cycle "requested by heartbeat" is still refused within 10 minutes of a message
    AC 6  /dream-cycle: synaptra unreachable still stops it

    python checks/dream/check_hand_run.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC = REPO / "src"
DREAM = SRC / ".claude" / "skills" / "dream" / "SKILL.md"
CYCLE = SRC / ".claude" / "skills" / "dream-cycle" / "SKILL.md"

# One sentence removed per mutant: (file, old, new, criteria that must fail).
MUTANTS = {
    "/dream has no owner exemption": (
        DREAM,
        "A bare `/dream` — typed\nby the owner — is the owner asking",
        "A `/dream` run is a run",
        ("AC 1",),
    ),
    "/dream no longer refuses automatic runs": (
        DREAM,
        "`requested by <requester>`",
        "`<requester>`",
        ("AC 2",),
    ),
    "/dream window changed": (
        DREAM,
        "last **10 minutes**",
        "last **1 minute**",
        ("AC 3",),
    ),
    "/dream-cycle has no owner exemption": (
        CYCLE,
        "A bare `/dream-cycle`, typed by the owner",
        "A `/dream-cycle`",
        ("AC 4",),
    ),
    "/dream-cycle no longer refuses the heartbeat's": (
        CYCLE,
        '`/dream-cycle "requested by\n   heartbeat"`',
        "`/dream-cycle`",
        ("AC 5",),
    ),
    "/dream-cycle drops the unreachable stop": (
        CYCLE,
        "**Synaptra unreachable**",
        "**Synaptra slow**",
        ("AC 6",),
    ),
}


def section(text: str, heading_re: str) -> str:
    """From a heading that matches to the next heading of the same or higher level."""
    m = re.search(rf"^(#+) {heading_re}.*?$", text, re.M)
    if not m:
        return ""
    level = len(m.group(1))
    rest = text[m.end() :]
    nxt = re.search(rf"^#{{1,{level}}} ", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def flat(s: str) -> str:
    return re.sub(r"\s+", " ", s)


def scenarios(dream: str, cycle: str) -> dict[str, tuple[bool, str]]:
    r: dict[str, tuple[bool, str]] = {}
    d = flat(section(dream, r"Refuses .*conversation"))
    c = flat(section(cycle, r"Hard stops"))

    r["AC 1"] = (
        "A bare `/dream` — typed by the owner" in d
        and "does not apply" in d
        and "pre-dream checkpoint" in d.split("does not apply", 1)[-1][:120],
        f"section found: {bool(d)}; owner exemption stated: {'typed by the owner' in d}",
    )
    r["AC 2"] = (
        "`requested by <requester>`" in d and "refuses and says why" in d,
        f"names the requested-by form: {'requested by <requester>' in d}; says why: {'says why' in d}",
    )
    r["AC 3"] = (
        "last **10 minutes**" in d,
        f"window text: {'last **10 minutes**' in d}",
    )
    r["AC 4"] = (
        "A bare `/dream-cycle`, typed by the owner" in c and "does not apply" in c,
        f"owner exemption stated: {'typed by the owner' in c}",
    )
    r["AC 5"] = (
        '`/dream-cycle "requested by heartbeat"`' in c
        and "10 minutes" in c
        and "refuse" in c,
        f"heartbeat form still refused: {'requested by heartbeat' in c}",
    )
    r["AC 6"] = (
        "**Synaptra unreachable**" in c,
        f"unreachable stop present: {'unreachable' in c}",
    )
    return r


def main() -> int:
    failed = 0
    print("== shipped files ==")
    real = scenarios(DREAM.read_text("utf-8"), CYCLE.read_text("utf-8"))
    for ac in sorted(real):
        ok, note = real[ac]
        print(f"  {'PASS' if ok else 'FAIL'}  {ac}  {note}")
        failed += not ok

    print("== each criterion bites ==")
    for name, (target, old, new, must_fail) in MUTANTS.items():
        text = target.read_text("utf-8")
        if old not in text:
            print(
                f"  FAIL  mutant '{name}': text to remove not found in {target.parent.name}"
            )
            failed += 1
            continue
        mutated = text.replace(old, new)
        got = scenarios(
            mutated if target == DREAM else DREAM.read_text("utf-8"),
            mutated if target == CYCLE else CYCLE.read_text("utf-8"),
        )
        for ac in must_fail:
            bit = not got[ac][0]
            print(f"  {'PASS' if bit else 'FAIL'}  '{name}' makes {ac} fail")
            failed += not bit

    print("\nOK" if not failed else f"\n{failed} check(s) failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
