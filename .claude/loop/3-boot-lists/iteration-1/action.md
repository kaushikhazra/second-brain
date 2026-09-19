# Action

**Cycle 4. `session-end`: handoff type-verification, and wiring the extended
`verify_memory.py` (both halves) into its own step.**

Cycles 1–3 built the hook exemption, `verify_memory.py`'s list half, `session-start`'s
fetch, and `init-brain`'s seeding round — 11/20. `session-end` is the last untouched
skill. AC 3's precedent (removed a stale mechanism, didn't just add) applies again
here: this cycle extends and corrects existing steps, it doesn't bolt on new ones
where an existing step already covers the ground.

Read the issue's criteria fresh (`gh issue view 3 -R kaushikhazra/second-brain`) before
the diff and before `logs/cycle-3.md`. Re-read `assumption.md` fresh.

## What changes in `session-end/SKILL.md`

Read the full current file first (already done this cycle, for scoping — re-read
fresh at the top of cycle 4 too, per discipline) — it has 5 steps: kill crons, store
learnings, store handoff, run the conformance scan, sign off.

1. **Step 3 (handoff)** — currently stores an `episodic` memory but doesn't say
   *through* `/create-memory` explicitly, and doesn't verify what landed. Add:
   store via `/create-memory` (AC 8, tags already correct: `end-of-day`, `handoff`,
   `resume-next-session`, the date), then **read it back**. If it landed `working`
   instead of the requested `episodic`, retype via `cm update --type episodic` and
   read back again to confirm (AC 9) — `observe.md`'s own warning: synaptra 2.0.0
   honors an explicit type, so this path won't fire in a normal run, but the
   instruction has to exist and be provable anyway, the same way #2 handled AC 7.

2. **Step 1 (crons)** — already kills every cron and verifies with a final
   `CronList`. AC 12 wants this **reported**, not just done — check whether step 5's
   sign-off already surfaces "crons killed" (it does, generically); make it specific
   ("cron list confirmed empty") rather than assumed done silently.

3. **Step 4 (the scan)** — currently only feeds the conformance-scan half of
   `verify_memory.py` (a bare `memory_list(state="active")` dump, no `resolved`
   map). Extend: after listing active memories, `memory_get` every id that appears
   in a `self-map`/`surface-map` holder's content (mirroring what
   `session-start` already does at boot — don't re-derive the id-collection logic,
   reference it), build the `"resolved"` map, write the fuller JSON, run
   `verify_memory.py`, and **print its full result** — both halves, per AC 13's
   literal text ("each list present exactly once, its count, every id resolving,
   and the conformance scan").

4. **AC 14** — a failed verify doesn't block the handoff. Check the ORDER: handoff
   (step 3) already runs before the scan (step 4), so this should already hold
   structurally — confirm, don't assume, and state it explicitly in step 4's text
   ("this step's findings are reported, never a reason to undo step 3").

5. **AC 20** — nothing about the lists is written at session end. Confirm by
   re-reading the whole file once finished: does anything call `/update-memory` or
   `/create-memory` with `self-map`/`surface-map` tags? It shouldn't — the surface
   map is issue #4's (the heartbeat's) to maintain, not this story's. A grep-based
   check (mirroring `check_session_start.py`'s fenced-block approach) can prove this
   structurally.

## Prove it

Structural checks where the claim is about the skill's own text (AC 12's reporting,
AC 20's "writes nothing to the lists"), same shape as `check_session_start.py`. For
AC 8/9/13/14 (actual runtime behavior — does the handoff really get stored, read
back, retyped if needed, and does the scan really run with both halves), decide
whether a scripted-agent run is warranted given the cost already spent this story
(~$1.38 so far) or whether a more targeted check suffices — `session-end` is easier
to isolate in a scratch project than `session-start` was (no interview to route
around), so a scripted run may be cheaper and more direct here than it was for
`init-brain`.

## Either way

Run `check_shapes.py`, `check_hooks.py`, `check_verify_memory.py`,
`check_session_start.py` — all four must still pass at their established counts
(5/5, 15/15, 11/11, 2/2).

## Commit, push, log, exit

Write `logs/cycle-4.md`. If this closes `session-end`, the only work left after this
cycle is proving `session-start`'s own runtime behavior (AC 10, 11, 18) — write
`action.md` for cycle 5 accordingly, or note if `session-end`'s proof work already
picked some of that up incidentally (init-brain's "Finish" hands off to
`session-start`, so this story's own scripted-agent runs may already be indirect
evidence worth checking before assuming nothing was gathered).
