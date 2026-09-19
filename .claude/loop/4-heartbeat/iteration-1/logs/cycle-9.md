# Cycle 9

**Branch**: `feature/4-heartbeat`, clean at start (cron-fired). **Clock**: 2026-09-19
22:11 +0530 at start, 22:20 +0530 at close. Well inside the 23:59 +0530 fail-safe.

Read `logs/cycle-8.md` first, then the issue's criteria fresh from GitHub — AC 4,
17, 18, 20 unchanged.

## A real multi-turn test, not a proxy

Checked `claude -p --help` before deciding on the proxy-prompt fallback action.md
allowed for — `--session-id` and `--resume` support genuine session continuity in
headless mode. Sanity-checked first (two quick turns outside the real test data):
told a fresh session "my favorite color is teal," then resumed the SAME session id
and asked it to recall that from conversation, not memory. It answered correctly
at a fraction of the first turn's cost (cache hit) — real context carry-over,
confirmed before building on it.

Built `check_heartbeat_ac4_ac17_ac18_scripted_agent.py`: eight sequential turns in
one real session (alternating ordinary chat and `"requested by cron"` beats),
verified from the store afterward, not the transcript.

## What actually happened, including a deviation from the plan

**Turn 1** (ordinary chat, a decision worth capturing) was stored immediately by
the chat turn itself, via the scratch project's own `/create-memory` routing rule —
not by the first heartbeat beat, as the test was designed to require. This means
AC 4's proof ended up testing something adjacent to but not identical to the
original plan: not "does beat 2 avoid re-capturing what beat 1 already captured,"
but "do beats 1–4, all of which have the decision in their session history, avoid
ever re-storing it." **Still real evidence, stated honestly rather than as the
originally-planned test**: verified against the store, exactly ONE memory exists
for the decision, across all four beats. No duplication.

**The quiet-count timeline shifted by one beat** for the same reason: beat 1
reported "quiet (1st in a row)" (nothing NEW to capture, since the decision was
already stored), so the third consecutive quiet beat landed at beat 3, not beat 4
as planned. Beat 3's own output: *"quiet cycle 3 reached; `/curiosity` isn't
present in this project, so no action taken and the quiet count resets to 0."*
Beat 4 then reported "quiet (1st in a row)" again — independent confirmation that
the reset from beat 3 genuinely took effect, not just that beat 3 claimed it would.

## Results

- **AC 4: MET** — verified against the store (exactly one memory for the decision,
  not duplicated across four beats sharing the same session history), with the
  caveat above stated plainly rather than overclaiming the originally-planned exact
  shape of the test.
- **AC 17: MET** — three consecutive quiet beats (1, 2, 3) correctly triggered the
  observation, evidenced by beat 3's own output and beat 4's fresh restart.
- **AC 18, inactive branch: MET** — `/curiosity` absent, the beat didn't error
  trying to invoke a missing skill and explicitly stated the reset. **Active
  branch: still untestable** — nothing exists to fire yet (issue #6). Recording
  this as a judgement call rather than counting AC 18 fully met on half its text:
  flagging to velasari rather than deciding unilaterally whether "provably correct
  on the branch that can currently exist" satisfies the criterion as written.

## AC 20 — stays text-only, a judgement call for velasari

"A beat that runs past its cron interval is not run twice; the next fire starts a
fresh beat." `SKILL.md`'s `## Failure` section states the reasoning (each cron fire
is its own fresh invocation; no persistent process to overrun). This is a claim
about how Claude Code's own cron scheduler behaves under overlap — not something a
`.claude/skills/heartbeat/` scripted-agent run can observe, since each run only
ever controls one `claude -p` invocation at a time, never the actual scheduler.
Testing it for real would mean creating overlapping crons in a live session and
watching for a double-fire, which risks interfering with this very loop's own
cron — not attempted. Recorded as text-only, not demonstrably met under this
story's own bar, rather than forced to a pass. Flagging to velasari: is the stated
reasoning sufficient to close this criterion, or does it need a different kind of
verification this loop can't produce alone?

## Regression check

`check_shapes.py` 5/5 · `check_hooks.py` 15/15 · `check_session_start.py` 2/2 ·
`check_verify_memory.py` 12/12 · `check_heartbeat.py` 3/3 — all pass.

## Criteria met, out of 20

Carried: AC 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 19. New this cycle:
**AC 4, AC 17.** AC 18's inactive branch demonstrated but not counted pending
velasari's ruling on partial-criterion credit. AC 20 stays open, architectural.

**18/20**, with two judgement calls (AC 18, AC 20) surfaced rather than
force-resolved.

## What moved

16 → 18. The multi-turn session-resume technique is new to this story and worked
cleanly on the first real attempt (after a cheap sanity check) — stronger evidence
than any single-shot proxy could have produced, at the cost of one design deviation
(turn 1's auto-store) that was reported honestly rather than smoothed over.

## Assumptions changed

None from the owner. This cycle's own finding (chat turns outside a heartbeat beat
also route through `/create-memory` per the scratch CLAUDE.md, which shifted the
quiet-count timeline) is noted here, not a contradiction of anything in
`assumption.md`.

## Next

This loop has not converged — two items remain judgement calls, not proven false.
`action.md` rewritten to report the full picture to velasari and ask for a ruling
on both: whether AC 18's inactive-branch proof is sufficient credit, and how (or
whether) AC 20 can be closed given its architectural nature. Fail-safe remains
2026-09-19 23:59 +0530; comfortably inside it.
