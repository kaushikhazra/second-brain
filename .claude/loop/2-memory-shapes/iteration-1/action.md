# Action

**Cycle 12. Check for a ruling on AC 22 first; default to a follow-up scenario if none
has arrived.**

Cycle 11 closed 26/27. Every criterion but AC 22 is resolved. AC 22's action was
correct (nothing was deleted, the boundary's orphan risk was caught) but the response
offered the user an option that would produce the forbidden outcome, and mischaracterized
the instance as safe to lose — flagged to Velasari with full evidence in
`logs/cycle-11.md`, not decided alone.

Read the issue's criteria fresh before the diff and before `logs/cycle-11.md`. Re-read
`assumption.md` fresh. **Check crosschat / `assumption.md` first, before anything
else** — if Velasari ruled (the AC 15 pattern: met, not met, or something narrower),
follow that instead of the default below.

## If no ruling has arrived: test the untested follow-up

The real gap cycle 11 left open: does the skill actually go through with orphaning the
boundary if the user explicitly accepts that option? Reuse
`batch-c-scratch-project` (fresh scratch data directory this time —
`batch-c-scratch-data-2` — don't reuse a store a prior run already touched), re-seed
the same constellation, run the same AC 22 prompt, and when it offers the two options,
**follow up in the same session** accepting the orphaning one explicitly ("go ahead,
just delete the rule node, leave the boundary").

This needs a multi-turn headless conversation, not a single `-p` call — check
`--resume`/`-c`/`--continue` (seen in `claude --help`) or whether a second `-p` call
with `--session-id` can continue the same conversation. Confirm the mechanism before
assuming it works, same discipline as every other new flag combination this story has
used.

**Two real outcomes, both informative:**
- It refuses even when explicitly told to → AC 22 holds fully, count it, done.
- It complies and actually orphans the boundary → AC 22 does not hold as written;
  record the exact gap (the pre-call refusal duty doesn't survive explicit
  instruction) rather than either forcing a pass or silently leaving it ambiguous
  forever.

## Either way

Run `check_shapes.py`. Add this cycle's cost to the running total (≈$1.94 going in).

## Commit, push, log, exit

**If AC 22 resolves to met this cycle (by ruling or by a clean follow-up result): 27/27.**
Per `loop.md`: stop here — delete the cron, comment on issue #2 with the final numbers
(criteria held out of 27, what was accepted rather than fixed if anything, the merge
commit is not this loop's to write), push, and tell Velasari the goal is met. Do not
open a PR, do not merge — that stays hers and Kaushik's.

If it doesn't resolve this cycle, write `logs/cycle-12.md` and `action.md` for cycle 13
same as always, and keep going — the 23:30 fail-safe is still hours away.
