# Action

**Cycle 2. Close the failure-handling gap, then start the headless-run batch.**

Read `logs/cycle-1.md` first — it found a real gap cycle 1's own plan didn't cover:
issue #4's AC 19 (synaptra unreachable → say so once, exit, no retry) and AC 20 (a
beat that overruns its cron interval is not run twice) have no home in the four
`observe.md`/`goal.md` ids, because they are failure-handling, not
observation-triggers-action pairs.

1. **`SKILL.md`** — add a short `## Failure` section (keep the whole file close to
   60 lines; trim if needed rather than let it grow unbounded):
   - AC 19: if a synaptra call fails because the server is unreachable, say so once
     (this is one of the three exceptions to the silence rule — state that
     explicitly, don't add a fourth) and stop the beat. No retry.
   - AC 20: each cron fire is its own beat: there is no persistent loop process to
     overrun, so "not run twice" is a property of how the beat starts, not something
     it tracks — state this plainly rather than inventing a lock file to guard a
     race that cron's own one-fire-one-invocation model doesn't have. If that
     reasoning turns out wrong (a fire can genuinely overlap a still-running one),
     say so instead of forcing the stated conclusion.

2. **Prove AC 19** with a headless run: point a scratch heartbeat invocation at a
   synaptra HTTP address nothing is listening on, confirm the beat's one line of
   output matches the say-once-and-stop text and that no second attempt follows.
   Record the actual output.

3. **Then start the headless-run batch from `observe.md`'s "five that will be got
   wrong"**, same batching discipline as #2's cycle 8: group what one scratch-agent
   run can exercise together.
   - **AC 5 + AC 12** first (the one `observe.md` calls out as easiest to get wrong):
     seed a scratch store with a closed surface-map entry, run a beat against an
     otherwise-empty window, assert from the store that the exit walk still removed
     the closed id even though nothing else fired.
   - **AC 8** next if time allows: feed a window with one item that merely happened
     and one that changes a decision, assert one store not two, and that its content
     carries the reason — same shape as #2's original AC 8 proof.

Never the live store — scratch under `C:/Projects/.tmp/second-brain-loop-4/`, started
and stopped explicitly around each use.

Do not touch `/update-memory` or `CLAUDE.md` this cycle either — the carve-out and the
routing row still come with the cycle that actually proves the surface-map write
(AC 14/15), not this one.

Re-run `check_shapes.py`, `check_hooks.py`, `check_session_start.py` and
`check_heartbeat.py` before closing the cycle — all four must still pass.

Commit on `feature/4-heartbeat`, push, write `logs/cycle-2.md`, write the next
`action.md`, send the one-line report to velasari, and exit.
