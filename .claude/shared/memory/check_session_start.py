#!/usr/bin/env python3
"""Structural check for issue #3's AC 3: "/session-start fetches both [lists] by tag
with memory_list, never with memory_self or memory_recall."

Grep-shaped, not a live/scratch synaptra session -- this is a claim about what the
skill's OWN TEXT instructs, not about synaptra's runtime behaviour. A scripted-agent
proof of the actual boot behaviour (does it really call memory_list and report
correctly) is a separate, heavier check for a later cycle; this one keeps the skill's
prose from silently regressing back to memory_self/memory_recall as the mechanism.

Usage: python check_session_start.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SKILL_FILE = (
    Path(__file__).resolve().parent.parent.parent
    / "skills"
    / "session-start"
    / "SKILL.md"
)

# A "live" use is memory_self(...) or memory_recall(...) NOT immediately preceded by a
# negation word on the same or previous few words -- approximated here by requiring the
# call appear inside a fenced code block (a real invocation) rather than prose.
FENCED_CALL_RE = re.compile(r"```\s*\n([^`]*?)\n```", re.MULTILINE | re.DOTALL)
FORBIDDEN_CALL_RE = re.compile(r"\bmemory_self\s*\(|\bmemory_recall\s*\(")
REQUIRED_CALL_RE = re.compile(r"\bmemory_list\s*\(\s*tags\s*=")


def main() -> int:
    if not SKILL_FILE.is_file():
        print(f"[FAIL] session-start SKILL.md not found at {SKILL_FILE}")
        return 1

    text = SKILL_FILE.read_text(encoding="utf-8")
    results: list[tuple[str, bool, str]] = []

    # AC3, positive: memory_list(tags=... appears as an actual fenced invocation,
    # at least twice (self map, surface map).
    fenced_blocks = FENCED_CALL_RE.findall(text)
    list_calls = [b for b in fenced_blocks if REQUIRED_CALL_RE.search(b)]
    ok1 = len(list_calls) >= 2
    results.append(
        (
            "AC3: memory_list(tags=...) used as the boot fetch, at least twice",
            ok1,
            f"found {len(list_calls)} fenced memory_list(tags=...) block(s)",
        )
    )

    # AC3, negative: memory_self(...) / memory_recall(...) never appear as an actual
    # fenced invocation (mentioning them in prose, to say "never use this", is fine
    # and expected -- only a call inside a code fence counts as "used as the mechanism").
    forbidden_calls = [b for b in fenced_blocks if FORBIDDEN_CALL_RE.search(b)]
    ok2 = len(forbidden_calls) == 0
    results.append(
        (
            "AC3: memory_self(...)/memory_recall(...) never invoked as the boot mechanism",
            ok2,
            f"forbidden fenced call(s) found: {forbidden_calls}"
            if forbidden_calls
            else "none found",
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
