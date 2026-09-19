# Cycle 1

**Branch**: `feature/4-heartbeat` (already checked out, shared working tree; clean at
start). **Clock**: 2026-09-19 20:06 +0530.

## Baseline (before writing anything)

- Current `.claude/skills/heartbeat/SKILL.md`: 133 lines. Describes a Haiku sub-agent
  dispatch and a prose `self-learning-surface-map` memory rebuilt by domain each beat —
  both go away in this story. Grep for `memory_store`/`memory_update`/`memory_delete`/
  `memory_archive`: none found — #2's reroute already left this file with no direct
  calls, it just still describes the old sub-agent/prose-map shape in prose.
- `check_shapes.py`: 5/5 pass. `check_hooks.py`: 15/15 pass. `check_session_start.py`:
  2/2 pass. No regression going in.
- `memory_guard.py`'s holder exemption, in two sentences: a sentinel file
  (`.claude/.list-holder-check.json`), written by the live session through its own
  already-open connection, tells the hook whether a reserved-tag holder already
  exists; the hook reads it once, allows exactly the one legitimate create-or-update
  call it names, and deletes it whether it allowed or refused. It only inspects a
  call's `tags` argument at all when that argument is actually passed — a
  content-only `memory_update` (the surface-map write this story plans) never
  triggers the reserved-tag check in the first place, so the sentinel path is not
  needed for that specific write.

## What was built, in action.md's order

1. **`.claude/skills/heartbeat/observe.md`** (101 lines) — four sections, ids
   `capture`, `correction`, `quiet-cycles`, `surface-map`, generalised from
   Velasari's own file (owner/brain, no names, no ids, no dates, no incidents).
   `surface-map` carries both triggers: something happened and is still open; and
   has something on the list closed — the second explicitly marked as firing even
   on an empty window.
2. **`.claude/skills/heartbeat/goal.md`** (155 lines) — the four matching sections.
   `capture` routes to `/create-memory`, restates none of its rules, carries the
   "would a future session be wrong without this" judgement and the
   episodic-not-working line for commitments. `correction` routes to
   `/create-memory` with the mechanism-not-event rule and the
   caught-and-fixed-in-window judgement. `quiet-cycles` fires `/curiosity` only if
   present and active, resets the count otherwise. `surface-map` carries the full
   entry test, the N≤25 ceiling as a ceiling not a floor, the every-beat exit walk,
   the content-only write, the read-back-and-state-count rule, and the self-map
   exclusion.
3. **`.claude/skills/heartbeat/SKILL.md`** (57 lines, under the 60-line target) —
   files table, observe → act steps with the stop-except-surface-map-exit-walk
   exception, the window, the invocation-source check, the silence rule with its
   three exceptions.
4. **`.claude/skills/heartbeat/check_heartbeat.py`** — asserts the three files exist
   (AC 1), the id pairing both ways (AC 2), and the AC 9 grep (no direct
   `memory_store`/`memory_update`/`memory_delete`/`memory_archive` anywhere under
   the heartbeat folder). Run: **3/3 pass.**
   - **AC 2 proven, not just asserted**: copied the three files to a scratch dir,
     appended an unmatched `id: unmatched-probe` section to the copy's
     `observe.md`, re-ran the script against the copy — it failed
     (`missing_in_goal=['unmatched-probe']`, exit 1) — then deleted the scratch
     copy. The pairing check is a real assertion.

## A gap the plan didn't cover, found while tallying

Issue #4's **Failure** section — AC 19 (synaptra unreachable: say so once, exit, no
retry) and AC 20 (a beat that overruns its interval is not run twice) — has no home
in the four `observe.md`/`goal.md` ids, and action.md's cycle-1 plan for `SKILL.md`
(files table, observe→act, window, invocation-source check, silence rule) didn't
name it either. These are cross-cutting failure-handling rules, not
observation-triggers-action pairs, so they don't fit the id-pairing model the other
four sections use. Not fixed this cycle — flagged here and carried into the next
`action.md` as its own step, rather than bolted on unreviewed at the end of this one.

## Criteria met, out of 20

**Only what a check proves, per `observe.md`'s bar** (mechanism/script, not "the
skill file says so"):

- **AC 1** — mechanism (`check_heartbeat.py`). MET.
- **AC 2** — mechanism (`check_heartbeat.py`, proven against an injected failure).
  MET.
- **AC 9** — mechanism (`check_heartbeat.py`'s grep). MET.

**3/20.** Everything else the new files state in prose (AC 3–8, 10–18) is written
but not yet demonstrated by a check or a headless run — that is deliberately not
counted yet, same discipline as #2 and #3. AC 19 and AC 20 are not yet addressed at
all (see the gap above).

## What moved

Went from a 133-line sub-agent-dispatch heartbeat describing a prose surface map, to
the three-file `observe.md`/`goal.md`/`SKILL.md` shape with a passing structural
check. 0/20 → 3/20 demonstrably met. No regression: #2's and #3's checks still pass
5/5, 15/15, 2/2.

## Assumptions changed

None. `assumption.md` stands as written.

## Next

`action.md` rewritten for cycle 2: add the AC 19/AC 20 failure-handling text to
`SKILL.md` (short — synaptra-unreachable and no-double-run rules), extend
`check_heartbeat.py` or add a sibling check for AC 19/20 where mechanically provable,
then start on the "five that will be got wrong": AC 5+12 and AC 8 headless runs
against a scratch store under `C:/Projects/.tmp/second-brain-loop-4/`.
