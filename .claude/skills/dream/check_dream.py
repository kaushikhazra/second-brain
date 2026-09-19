#!/usr/bin/env python3
"""Issue #5 -- structural checks for `.claude/skills/dream/SKILL.md`:

- AC 6: no INSTRUCTION to call a raw `memory_archive`, `memory_update` or
  `memory_store` -- the criterion's own three names, exactly, no more and no
  fewer (velasari's ruling, issue #5 cycle 3). A prohibition sentence naming one
  is fine (e.g. "the dream contains no direct call to memory_archive"); only a
  call-shaped instruction (`memory_archive(id)`, or the bare name immediately
  followed by an open paren) counts against this. Same call-vs-mention
  distinction `check_heartbeat.py`'s AC 9 grep already draws. `memory_relate` and
  `memory_unrelate` are deliberately NOT in this list (ruled on, not an
  oversight); `memory_delete` is deliberately not here either, despite CLAUDE.md's
  own standing rule against it, because that protection already exists
  project-wide in `check_shapes.py`'s AC 23 scan -- see the comment on
  `FORBIDDEN_CALLS` below for both.
- AC 14: nothing schedules a dream -- no `CronCreate` call anywhere in the skill.
- AC 7 / AC 15: the skill states its retrievability threshold and its
  active-conversation window as explicit numbers, not "a while" or "recently."

Pure text check, no synaptra I/O, live or scratch. This is a structural proof, not a
behavioral one -- it tells you what the skill's OWN TEXT currently instructs, not
whether a live dream run actually behaves that way (a scripted-agent run is the
heavier, separate proof for that, built in a later cycle once the acts are edited).

Usage: python check_dream.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SKILL_FILE = Path(__file__).resolve().parent / "SKILL.md"

## Why memory_relate and memory_unrelate are NOT in this list (cycle 2's finding)
##
## AC 6's own enforcement sentence names three tools: memory_archive, memory_update,
## memory_store -- not memory_relate or memory_unrelate. This is not an omission:
## /create-memory itself calls memory_relate directly, as part of writing a NEW
## memory's own constellation edges (step 6, "Link it") -- there is no standalone
## "/create-memory relate mode" for linking two memories it did not just create, and
## inventing one would mean editing one of the four memory skills, which is out of
## this story's scope. The dream's own Act 4 keeps direct memory_relate/
## memory_unrelate calls, held to the SAME discipline /create-memory's step 6
## documents (full uuids, the closed rel_type vocabulary) -- mechanically backstopped
## by memory_guard.py's existing AC 26 rule regardless of which skill's text calls it.
## Ruling, issue #5 cycle 3 (velasari): confirmed -- Act 4 keeps them. "Two
## conditions, both already true, keep them stated in Act 4: full uuids only, which
## the hook enforces, and the edge-count verification after each batch."
##
## FORBIDDEN_CALLS matches AC 6's own enforcement sentence EXACTLY -- three names,
## not four. memory_delete is deliberately not here even though CLAUDE.md's own
## standing rule forbids calling it directly anywhere: that protection already
## exists, project-wide, in check_shapes.py's AC 23 scan (issue #2), which covers
## every `*/SKILL.md` outside the four memory skills, dream included. Adding a
## fourth name here would duplicate a check that already exists elsewhere and claim
## this script tests something AC 6 itself does not ask for.
FORBIDDEN_CALLS = (
    "memory_archive",
    "memory_update",
    "memory_store",
)
CALL_RE = {call: re.compile(rf"\b{call}\s*\(") for call in FORBIDDEN_CALLS}

# A CronCreate call whose prompt argument names /dream -- NOT any CronCreate call at
# all (the dream's own Act 6 legitimately recreates the heartbeat cron; that is not
# "scheduling a dream" and must not trip this check).
CRON_DREAM_RE = re.compile(r"CronCreate\s*\([^)]*?/dream", re.IGNORECASE | re.DOTALL)

# AC 7: a decimal retrievability value (e.g. 0.2), specifically near both
# "retrievability" and "archiv" -- narrower than "any number near the word
# threshold", which false-matched an unrelated "retrievability ~ 0" example
# describing decay in general, nowhere near an actual archive rule.
AC7_RE = re.compile(
    r"archiv\w*.{0,120}retrievability.{0,40}\b0\.\d+\b"
    r"|retrievability.{0,120}archiv\w*.{0,40}\b0\.\d+\b",
    re.IGNORECASE | re.DOTALL,
)

# AC 15: a number of minutes, specifically near "active conversation" -- narrower
# than "any number near the word minutes", which false-matched the heartbeat's
# unrelated 30-minute cadence mentioned in the intro. `\s+` between "active" and
# "conversation" (not a literal space) because markdown line-wrapping can put a
# newline there without changing the phrase's meaning -- a text check should
# survive reflow, not depend on it.
AC15_RE = re.compile(
    r"active\s+conversation.{0,80}\b\d+\s*minutes?\b"
    r"|\b\d+\s*minutes?\b.{0,80}active\s+conversation",
    re.IGNORECASE | re.DOTALL,
)


def main() -> int:
    results: list[tuple[str, bool, str]] = []

    if not SKILL_FILE.is_file():
        print(f"[FAIL] dream SKILL.md not found at {SKILL_FILE}")
        return 1

    text = SKILL_FILE.read_text(encoding="utf-8")

    # AC 6
    found_calls = [call for call, pattern in CALL_RE.items() if pattern.search(text)]
    ok6 = not found_calls
    results.append(
        (
            "AC6: no instruction to call a raw synaptra tool (prohibition sentences allowed)",
            ok6,
            "clean" if ok6 else f"found call-shaped instruction(s): {found_calls}",
        )
    )

    # AC 14: no CronCreate call whose prompt names /dream. The skill's own Act 6
    # legitimately recreates the HEARTBEAT cron -- that is not this criterion's
    # concern and must not trip this check.
    ok14 = not CRON_DREAM_RE.search(text)
    results.append(
        (
            "AC14: nothing schedules a dream (no CronCreate call naming /dream)",
            ok14,
            "clean"
            if ok14
            else "found a CronCreate(...) call whose prompt names /dream",
        )
    )

    # AC 7: an archive threshold stated as a decimal retrievability value, near
    # both "retrievability" and "archiv" -- not just any number near either word
    # alone (which false-matched an unrelated retrievability example in Act 1).
    ok7 = bool(AC7_RE.search(text))
    results.append(
        (
            "AC7: the archive threshold is stated as an explicit retrievability number",
            ok7,
            "found"
            if ok7
            else "no decimal retrievability value found near an archive rule",
        )
    )

    # AC 15: an active-conversation window stated as a number of minutes, near the
    # phrase "active conversation" specifically -- not just any nearby "minutes"
    # (which false-matched the heartbeat's unrelated 30-minute cadence).
    ok15 = bool(AC15_RE.search(text))
    results.append(
        (
            "AC15: the active-conversation window is stated as an explicit number of minutes",
            ok15,
            "found" if ok15 else "no minute count found near 'active conversation'",
        )
    )

    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")

    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n{passed}/{len(results)} of this script's criteria pass.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
