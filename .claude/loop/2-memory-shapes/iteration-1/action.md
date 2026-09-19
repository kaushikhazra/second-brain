# Action

**Cycle 10. Batch B — AC 13, AC 15 (`/read-memory`'s tool-naming and boundary-first
discipline).**

Batch A (cycle 9) proved AC 5, 11, 17, 20 — 22/27 total. Same methodology, reused: a
scratch project, seed directly (never through the agent), run small focused headless
scenarios, verify against ground truth where the criterion is about *stored state*, and
say plainly when a criterion is about *order of operations during the response* instead
— cycle 9 already hit this once (AC 20) and counted it on transcript evidence with the
caveat stated. AC 15 is the same kind of claim, more so: "pulls the boundary **before**
the rule is applied" is entirely about sequencing inside one response, not anything a
final store state can show.

Read the issue's criteria fresh (`gh issue view 2 -R kaushikhazra/second-brain`) before
the diff and before `logs/cycle-9.md`. Re-read `assumption.md` fresh — check whether
Velasari corrected the AC 11 batching call before proceeding further with the pattern.

## 1. Solve the sequencing-evidence question before building

`--output-format json` (used for every run so far) only returns a final summary — no
per-turn tool-call trace. Check `claude -p --help` again for `--output-format
stream-json` (seen in the help text, not yet used) and `--include-hook-events` /
`--forward-subagent-text` — one of these should expose the actual sequence of tool
calls (does `memory_recall`/`memory_related` happen, then does the response text
reference the boundary, before the rule is stated). Test the shape on a throwaway
prompt first, the same way `-p`'s flags were confirmed before Batch A, rather than
assuming a format from the flag name alone.

If no reasonably reachable output actually exposes ordering, say so plainly and score
AC 15 the way AC 20 was scored last cycle — on the response text's own structure
(does the boundary appear before the rule is stated, in the text itself) as the best
available evidence, not a manufactured proof it doesn't have.

## 2. Build the scratch project

`read-memory` + `create-memory` (needed to seed a `learning` with a boundary — seed
directly via `cm`, not through the agent, same as Batch A). Fresh scratch data
directory, distinct from `batch-a-scratch-data` and `ac8-scratch-data`.

Seed one `learning` constellation directly: an instance node (what happened,
verbatim-ish), a bare procedure node (the rule), a boundary node (when it does NOT
apply) — `instance —supports→ procedure`, `boundary —part_of→ procedure`, all three the
same store type.

## 3. Run the scenario(s)

Ask a question that should land on the instance via recall. Check:
- **AC 13**: does the response say which retrieval tool it used?
- **AC 15**: does the boundary get pulled (referenced) before the rule is stated as
  applying — in the response text's own order, and in the tool-call sequence if step 1
  found a way to see it?

## 4. Verify, record, keep the running cost total

Ground-truth where possible (nothing new should be *stored* by a read-only scenario —
confirm the store is unchanged after, which is itself a useful check: a `/read-memory`
call that accidentally wrote something would be a real bug). Add this cycle's cost to
the running total from `logs/cycle-9.md` (≈$1.04 so far).

## 5. Commit, push, log, write cycle 11's action.md, exit

Queue Batch C (AC 16, 21, 22) for cycle 11 if Batch B doesn't leave time to start it —
same "one thing well" discipline as every prior cycle.
