#!/usr/bin/env python3
"""Structural check for issue #3's session-end changes: AC 13 (both halves printed),
AC 14 (a failed verify never blocks the handoff), AC 20 (nothing writes to the
lists), plus AC 23 self-check (no forbidden substring, the same class of regression
cycle 3 caught in init-brain).

Grep-shaped, not a live/scratch synaptra session -- claims about what the skill's
OWN TEXT instructs. Runtime behavior (does the handoff actually get stored, read
back, retyped if needed) is a separate, heavier check.

Usage: python check_session_end.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SKILL_FILE = (
    Path(__file__).resolve().parent.parent.parent
    / "skills"
    / "session-end"
    / "SKILL.md"
)
FORBIDDEN_RE = re.compile(r"\bmemory_store\b|\bmemory_update\b|\bmemory_delete\b")


def main() -> int:
    if not SKILL_FILE.is_file():
        print(f"[FAIL] session-end SKILL.md not found at {SKILL_FILE}")
        return 1

    text = SKILL_FILE.read_text(encoding="utf-8")
    results: list[tuple[str, bool, str]] = []

    # AC23 self-check: no forbidden substring anywhere (this skill is not one of the
    # four memory skills, so it gets none of the exemptions check_shapes.py grants them).
    forbidden = FORBIDDEN_RE.findall(text)
    ok0 = len(forbidden) == 0
    results.append(
        (
            "AC23: no forbidden direct-call substring",
            ok0,
            f"found: {forbidden}" if forbidden else "clean",
        )
    )

    # AC13: the skill instructs printing BOTH halves of verify_memory.py's result --
    # look for language naming the two-list findings specifically, not just "run the
    # script" (which cycle 1-era text already had for the conformance half alone).
    ok1 = bool(re.search(r"every id resolving", text)) and bool(
        re.search(r"conformance scan", text)
    )
    results.append(
        (
            "AC13: both halves (list findings + conformance) named as printed",
            ok1,
            "found both phrases" if ok1 else "missing one or both",
        )
    )

    # AC13: builds a 'resolved' map before running the script (not just the bare
    # conformance-scan-only JSON from issue #2's original step).
    ok2 = "resolved" in text and "memory_get" in text
    results.append(
        (
            "AC13: builds the 'resolved' map (memory_get per listed id)",
            ok2,
            "present" if ok2 else "missing",
        )
    )

    # AC14: an explicit statement that step 4 does not block/undo step 3.
    ok3 = bool(re.search(r"never a reason to undo or withhold", text)) or bool(
        re.search(r"does not block", text)
    )
    results.append(
        (
            "AC14: explicit non-blocking statement present",
            ok3,
            "found" if ok3 else "missing",
        )
    )

    # AC9: retype-if-working path stated, with a second read-back after the retype.
    ok4 = "working" in text and "--type episodic" in text and text.count("read") >= 2
    results.append(
        (
            "AC9: retype-if-working + second read-back stated",
            ok4,
            "found" if ok4 else "missing",
        )
    )

    # AC20: this step is explicitly stated read-only with respect to the lists.
    ok5 = (
        bool(re.search(r"read-only", text, re.IGNORECASE))
        and "never writes anything" in text
    )
    results.append(
        (
            "AC20: step 4 explicitly stated read-only re: the lists",
            ok5,
            "found" if ok5 else "missing",
        )
    )

    passed = 0
    for name, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        print(f"[{status}] {name}: {detail}")
    print(f"\n{passed}/{len(results)} of this script's criteria pass.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
