# Cycle 3

**Branch**: `feature/5-dream`, clean at start. **Clock**: 2026-09-19 22:59 +0530.
Well inside the 2026-09-20 02:00 +0530 fail-safe.

Not cron-fired — velasari's ruling on cycle 2's Act 4 judgement call arrived
before the next scheduled fire, and applying a completed ruling promptly mattered
more than waiting. Treated as this cycle's work, per the same pattern issue #4's
loop used when a crosschat message arrived mid-idle; cycle 2's originally-planned
next work (AC 3, 9, 16, 17) moves to cycle 4.

## The ruling

velasari confirmed cycle 2's reading: `memory_relate` and `memory_unrelate` may
stay direct calls in the dream. AC 6 names exactly three tools (`memory_archive`,
`memory_update`, `memory_store`); relating is not one of them, there is no skill
whose job is edge surgery between existing memories, and inventing one to satisfy
a criterion that does not ask for it would be the wrong move. Two conditions,
both already true in Act 4, keep the direct calls sound: full uuids only
(`memory_guard.py`'s AC 26 rule enforces this regardless of which skill's text
calls it) and the edge-count verification after each relate batch (Act 4 step 6,
already present).

**Instruction**: make `check_dream.py`'s AC 6 grep match the criterion's three
names exactly — "so it neither passes on a loophole nor fails on relate."

## The fix

`check_dream.py`'s `FORBIDDEN_CALLS` narrowed from four tools (cycle 2 had
`memory_archive`, `memory_update`, `memory_store`, `memory_delete`) to exactly
the three AC 6 names. Checked before removing `memory_delete`, not assumed safe
to drop: `check_shapes.py`'s AC 23 scan (issue #2) already covers every
`*/SKILL.md` outside the four memory skills — dream included — for exactly
`memory_store`/`memory_update`/`memory_delete`. Removing the fourth name from
`check_dream.py`'s own list creates no actual gap; that protection already exists,
project-wide, elsewhere. Both docstrings updated to state the reasoning and cite
the ruling, so this doesn't read as an unexplained narrowing to a future reader.

## Regression check

`check_dream.py` 4/4 (unchanged — AC 6 still passes correctly, now testing
exactly what the criterion says). Full line: `check_shapes.py` 5/5 ·
`check_hooks.py` 27/27 · `check_session_start.py` 2/2 · `check_verify_memory.py`
12/12 · `check_heartbeat.py` 3/3 — all pass.

## Criteria met, out of 17

Unchanged: **7/17** (AC 1, 2, 6, 7, 8, 14, 15). This cycle corrected what AC 6's
own check tests, not the count.

## What moved

Nothing numerically — a precision fix, not new ground. Worth logging as its own
cycle anyway: a check that tests more than its named criterion is its own kind of
false confidence, the mirror image of a check that tests less. Both are worth
catching.

## Assumptions changed

Act 4's design is now settled, not a standing judgement call — velasari's ruling
closes it. Do not re-open without a genuinely new reason.

## Next

`action.md` unchanged in substance, retargeted to cycle 4: AC 3 (the non-zero-exit
branch, untested), AC 9 (retype via `cm` CLI, read back — check whether
`/update-memory`'s existing text already covers this before building anything
new), AC 16 (an abort leaves the store exactly as it was), AC 17 (synaptra
unreachable, stops before any backup).
