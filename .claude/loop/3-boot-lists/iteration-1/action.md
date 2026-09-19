# Action

**Cycle 5. `session-start`'s own live boot behavior — AC 10, 11, 18. The last three.**

Cycles 1–4 built and proved every criterion except these three. All three are about
`session-start`'s actual runtime behavior (handoff-by-recency, no-handoff reporting,
synaptra-unreachable handling) — `session-start`'s prose was written and proved
structurally in cycle 2 (AC 3), but no live run has specifically targeted these three.
`init-brain`'s cycle-3 runs handed off into `session-start` at the end and it greeted
correctly, which is suggestive but not proof of these specific behaviors.

Read the issue's criteria fresh (`gh issue view 3 -R kaushikhazra/second-brain`) before
the diff and before `logs/cycle-4.md`. Re-read `assumption.md` fresh.

## Three small scenarios, not one contrived prompt — same lesson as issue #2's Batch A

Build `session-start-scratch-project/`: `create-memory` + `session-start` + the
`PreToolUse` hook + settings.json, with `persona.md`/`user.md` pre-existing (so
`session-start`'s own step 1 has something real to adopt, without needing
`init-brain`'s interview).

1. **AC 10 (most recent handoff by `created_at`)**: seed a self-map and surface-map
   (reuse cycle 4's seeding pattern) plus **two** handoff memories with different
   `created_at` timestamps and clearly different content ("yesterday's handoff" vs
   "today's handoff"). Run `session-start`, check it picked the newer one — verify
   against which one it actually references in its own report, not just that it ran.
2. **AC 11 (no handoff yet)**: same self-map/surface-map seed, **no** handoff memory
   at all. Run `session-start`, confirm it reports "no handoff yet" (or equivalent)
   and continues — check the run completes cleanly (persona adopted, lists loaded),
   not that it errors or stalls.
3. **AC 18 (synaptra unreachable)**: harder to stage — this needs the `mcp__synaptra__*`
   tools to be genuinely absent or erroring, not just an empty store. Investigate
   before assuming a mechanism: does `--mcp-config` pointing at a deliberately-broken
   server command (e.g. a nonexistent executable path) produce a clean "tools
   unavailable" condition `session-start` can detect via its own step 2 check, or does
   `claude -p` itself fail to start at all in that case? Test small before building
   the full scenario around it. If genuinely unstageable within reasonable effort,
   say so plainly and record what was tried — same discipline as issue #2's cycle 8
   when a proof route turned out harder than expected.

Verify each scenario against the actual store where applicable (AC 10 especially —
confirm which handoff's content actually appears in the session's own summary,
against the ground truth of which one has the later `created_at`), and against the
transcript where the store can't independently confirm behavior (same caveat class
as cycle 4's AC 12).

## Either way

Run all five existing checks (`check_shapes.py`, `check_hooks.py`,
`check_verify_memory.py`, `check_session_start.py`, `check_session_end.py`) — all
must still pass at their established counts.

## Commit, push, log, exit

**If all three land: 20/20.** Per `loop.md`: stop here — delete the cron, comment on
issue #3 with the final numbers (criteria held out of 20, total scripted-agent cost
across the whole story, what was accepted rather than fixed if anything), push, tell
Velasari the goal is met. No PR, no merge.

If AC 18 genuinely can't be staged this cycle, land AC 10/11, record AC 18's honest
status, and write `action.md` for cycle 6 with whatever's actually left — don't force
a fourth scenario into this cycle just to close the number if the third one turns out
to need real investigation first.
