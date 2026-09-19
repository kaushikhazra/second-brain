# Action

**Cycle 11. Batch C — AC 16, AC 21, AC 22 (refuse a tidiness-only update, archive-vs-delete
judgment, refuse partial constellation removal).**

Batch B (cycle 10) closed AC 13 cleanly and produced genuinely mixed evidence for AC 15
— recorded, not forced into a verdict. 23/27, plus one documented-but-uncounted
criterion. This is the last batch; after this cycle every one of the nine is either
proved, or has real recorded evidence either way.

Read the issue's criteria fresh (`gh issue view 2 -R kaushikhazra/second-brain`) before
the diff and before `logs/cycle-10.md`. Re-read `assumption.md` fresh — check whether
Velasari weighed in on AC 15's mixed result before deciding how to record it further.

## Build

`update-memory` + `delete-memory` (+ `create-memory` to seed). Fresh scratch data
directory (`batch-c-scratch-data`). Use `--output-format json` (plain, like AC 8 and
Batch A) unless a scenario turns out to need sequencing evidence the way AC 15 did —
judge per scenario, don't default to `stream-json` everywhere out of habit.

## Three scenarios, seeded directly, never through the agent

1. **AC 16** — seed one ordinary `fact`. Ask for a purely cosmetic edit (e.g. a typo
   fix that changes nothing substantive). Expect: refusal, with a stated reason
   (stability-reinforcement cost, not just "I don't feel like it"). Verify against the
   store: content unchanged, no version bump.
2. **AC 22** — seed a full `learning` constellation (instance + procedure + boundary,
   same pattern as Batch B). Ask it to remove just the procedure node, leaving the
   instance and boundary. Expect: refusal, citing the constellation rule. Verify: all
   three nodes still active afterward.
3. **AC 21** — seed two cases: one superseded-but-was-true fact (a measurement replaced
   by a newer one) and one never-true fact (asserted something that was wrong from the
   start). Ask it to clean up both. Expect: the superseded one archived (not deleted),
   the never-true one deleted, and it says which operation applies to which and why.
   Verify: one ends up `state=archived` (still `memory_get`-able, restorable), the
   other genuinely gone (`memory_get` fails).

Three small scenarios, not one contrived prompt — same lesson from Batch A.

## Verify against ground truth, keep the running cost total

Running total before this cycle: ≈$1.16 (cycles 8–10). Add this cycle's cost.

## Commit, push, log, exit

This closes Batch C. Write `logs/cycle-11.md` summing up where all 27 stand: met
cleanly, met with a stated caveat (AC 20, AC 14, AC 25 precedent), and AC 15's mixed
evidence specifically — don't let it quietly vanish from the tally just because it
isn't a clean number. Write `action.md` for cycle 12 based on what's actually left,
not assumed — if AC 15 is still the only unresolved one, cycle 12's job is deciding
what to do about a criterion with real evidence on both sides, not building anything
new.
