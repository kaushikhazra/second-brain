#!/usr/bin/env python3
"""Issue #87 proofs: the brain's documentation agrees with itself and with the synaptra it pins.

Reads the shipped markdown (src/) and extracts the claims that more than one file makes, then
compares them. Each criterion is shown to bite: the same read runs on copies of the files with
the old, contradicting text put back, and the named criteria must FAIL.

    AC 1  src/CLAUDE.md does not recommend `cm backup`; /dream's checkpoint is a file copy
    AC 2  src/CLAUDE.md does not say /session-start fires memory_self
    AC 3  create-memory, memory-shapes.md and dream list the same eight rel_type values
    AC 4  the synaptra version memory-shapes.md says it was verified against is SYNAPTRA_VERSION
    AC 5  initial stability in days is the same in CLAUDE.md, memory-shapes.md and create-memory
    AC 6  no shipped markdown describes a type's lifespan in words that differ from those figures
    AC 7  no restart instruction in update, init-brain, session-start or transcribe names a launcher

    python checks/docs/check_docs_agree.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC = REPO / "src"
CLAUDE_MD = SRC / "CLAUDE.md"
SHAPES = SRC / ".claude" / "shared" / "memory" / "memory-shapes.md"
CREATE = SRC / ".claude" / "skills" / "create-memory" / "SKILL.md"
DREAM = SRC / ".claude" / "skills" / "dream" / "SKILL.md"
PIN = SRC / "SYNAPTRA_VERSION"
UPDATE = SRC / ".claude" / "skills" / "update" / "SKILL.md"
INIT = SRC / ".claude" / "skills" / "init-brain" / "SKILL.md"
START = SRC / ".claude" / "skills" / "session-start" / "SKILL.md"
TRANSCRIBE = SRC / ".claude" / "skills" / "transcribe" / "SKILL.md"
LAUNCH = SRC / ".claude" / "skills" / "transcribe" / "scripts" / "launch.py"
RESTART_FILES = [UPDATE, INIT, START, TRANSCRIBE, LAUNCH]
RESTART_VERB = re.compile(r"\b(restart|start (it )?again|start the brain)\b", re.I)

REL_TYPES = {
    "causes",
    "follows",
    "contradicts",
    "supports",
    "relates_to",
    "supersedes",
    "part_of",
    "describes",
}
TYPES = {"working", "episodic", "semantic", "procedural", "person", "identity"}
LIFESPAN_WORDS = re.compile(
    r"\b(a fortnight|a season|about a year|18 months|year-lived|fortnight-lived)\b",
    re.I,
)

# One old contradiction put back per mutant: (file, text now, text before, criterion that must fail).
MUTANTS = {
    "CLAUDE.md recommends cm backup again": (
        CLAUDE_MD,
        "`cm backup` is not used",
        "`cm backup` is used",
        "AC 1",
    ),
    "CLAUDE.md says session-start fires memory_self": (
        CLAUDE_MD,
        "`memory_self` is a ranked *search*",
        "`memory_self` is fired by `/session-start`, a ranked *search*",
        "AC 2",
    ),
    "dream's rel_type list loses describes": (
        DREAM,
        "`part_of`,\n   `describes`.",
        "`part_of`.",
        "AC 3",
    ),
    "memory-shapes says it was verified against 2.0.0": (
        SHAPES,
        "synaptra `2.1.1`",
        "synaptra `2.0.0`",
        "AC 4",
    ),
    "create-memory disagrees on a stability figure": (
        CREATE,
        "`procedural` 60.0",
        "`procedural` 30.0",
        "AC 5",
    ),
    "create-memory gives a lifespan in words": (
        CREATE,
        "The larger the number",
        "A fortnight for episodic. The larger the number",
        "AC 6",
    ),
    "update tells the owner to restart with a launcher": (
        UPDATE,
        "4. Restart the brain",
        "4. Restart Claude with brain.bat",
        "AC 7",
    ),
    "init-brain's restart gate names a launcher": (
        INIT,
        "restart the\nbrain",
        "start it again with `brain.bat` (restart the\nbrain",
        "AC 7",
    ),
    "the transcribe error text names a launcher": (
        LAUNCH,
        'Restart the brain "',
        'Start the brain with brain.bat "',
        "AC 7",
    ),
}


def flat(s: str) -> str:
    return re.sub(r"\s+", " ", s)


def rel_types(text: str) -> set[str]:
    """The backticked words from the first `causes` to the end of its sentence."""
    start = text.find("`causes`")
    if start < 0:
        return set()
    sentence = re.split(r"\.\s", text[start:], maxsplit=1)[0]
    return set(re.findall(r"`(\w+)`", sentence))


def stability_pairs(text: str) -> dict[str, float]:
    return {
        m.group(1): float(m.group(2))
        for m in re.finditer(r"`(\w+)`\s+([0-9]+\.[0-9]+)", text)
    }


def table_stability(text: str) -> dict[str, float]:
    return {
        m.group(1): float(m.group(2))
        for m in re.finditer(r"^\| `(\w+)` \|.*\| ([0-9.]+) \|\s*$", text, re.M)
    }


def scan(
    files: dict[Path, str], pin: str, other_md: dict[Path, str]
) -> dict[str, tuple[bool, str]]:
    r: dict[str, tuple[bool, str]] = {}
    claude, shapes, create, dream = (
        files[p] for p in (CLAUDE_MD, SHAPES, CREATE, DREAM)
    )

    sentences_cm = [s for s in re.split(r"(?<=\.)\s", flat(claude)) if "cm backup" in s]
    r["AC 1"] = (
        bool(sentences_cm)
        and all("`cm backup` is not used" in s for s in sentences_cm)
        and "file copy" in flat(claude),
        f"sentences naming cm backup: {len(sentences_cm)}, all say it is not used: "
        f"{all('`cm backup` is not used' in s for s in sentences_cm)}",
    )

    m = re.search(r"- \*\*Self\*\*:.*?(?=\n- \*\*)", claude, re.S)
    bullet = flat(m.group(0)) if m else ""
    r["AC 2"] = (
        bool(bullet)
        and "fired by" not in bullet.lower()
        and "memory_list" in bullet
        and "self map" in bullet,
        f"Self bullet: {bullet[:140]!r}",
    )

    sets = {
        p.parent.name if p.name == "SKILL.md" else p.name: rel_types(t)
        for p, t in ((CREATE, create), (SHAPES, shapes), (DREAM, dream))
    }
    r["AC 3"] = (
        all(s == REL_TYPES for s in sets.values()),
        "; ".join(
            f"{k}: missing {sorted(REL_TYPES - v)} extra {sorted(v - REL_TYPES)}"
            for k, v in sets.items()
        ),
    )

    mv = re.search(r"verified\s+against\s+synaptra\s+`?(\d+\.\d+\.\d+)`?", shapes)
    r["AC 4"] = (
        bool(mv) and mv.group(1) == pin,
        f"memory-shapes says {mv.group(1) if mv else 'nothing'}, SYNAPTRA_VERSION is {pin}",
    )

    sect = re.search(
        r"### 3\. Choose the store type.*?(?=\n- \*\*`identity`)", create, re.S
    )
    tbl = table_stability(claude)
    shp = stability_pairs(shapes.split("Initial stability by type", 1)[-1][:400])
    crt = stability_pairs(sect.group(0) if sect else "")
    r["AC 5"] = (
        set(tbl) == TYPES and tbl == shp == crt,
        f"CLAUDE.md {tbl} | memory-shapes {shp} | create-memory {crt}",
    )

    hits = [
        f"{p.relative_to(SRC).as_posix()}: {m.group(0)!r}"
        for p, t in {**files, **other_md}.items()
        for m in LIFESPAN_WORDS.finditer(t)
    ]
    r["AC 6"] = (not hits, f"lifespan prose found: {hits or 'none'}")

    named_launcher = [
        f"{p.relative_to(SRC).as_posix()}: {flat(s)[:80]!r}"
        for p in RESTART_FILES
        for s in re.split(r"(?<=[.!?:])\s", flat(files[p]))
        if ".bat" in s and RESTART_VERB.search(s)
    ]
    r["AC 7"] = (
        not named_launcher,
        f"restart sentences that name a launcher: {named_launcher or 'none'}",
    )
    return r


def main() -> int:
    named = [CLAUDE_MD, SHAPES, CREATE, DREAM, *RESTART_FILES]
    files = {p: p.read_text("utf-8") for p in named}
    pin = PIN.read_text("utf-8").strip()
    other = {
        p: p.read_text("utf-8")
        for p in SRC.rglob("*.md")
        if p not in files and ".update-backup" not in p.as_posix()
    }

    failed = 0
    print("== shipped files ==")
    real = scan(files, pin, other)
    for ac in sorted(real):
        ok, note = real[ac]
        print(f"  {'PASS' if ok else 'FAIL'}  {ac}  {note}")
        failed += not ok

    print("== each criterion bites ==")
    for name, (target, now, before, ac) in MUTANTS.items():
        if now not in files[target]:
            print(
                f"  FAIL  mutant '{name}': text to put back not found in {target.name}"
            )
            failed += 1
            continue
        mutated = {**files, target: files[target].replace(now, before)}
        got = scan(mutated, pin, other)
        bit = not got[ac][0]
        print(f"  {'PASS' if bit else 'FAIL'}  '{name}' makes {ac} fail")
        failed += not bit

    print("\nOK" if not failed else f"\n{failed} check(s) failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
