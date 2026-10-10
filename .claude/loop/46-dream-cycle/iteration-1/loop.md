# Loop

```
Goal:                goal.md          (immutable)
Observe rules:       observe.md       (immutable)
Assumptions:         assumption.md
Action:              action.md
Artifact under test: .claude/skills/dream-cycle/ (new) · .claude/shared/activation.py ·
                     heartbeat/goal.md + observe.md · checks/dream-cycle/
Branch:              feature/46-dream-cycle
Issue:               https://github.com/kaushikhazra/second-brain/issues/46

Cron every 15 minutes (Kaushik's call), one cycle per fire. One session does everything,
one check at a time: no subagents, no parallel workers, no spawned `claude -p`.

ONE cycle per run:
  - Action:  do what action.md asks
  - Observe: check against the goal, using observe.md
  - If goal met:     comment on issue #46 with the numbers (criteria met out of 11,
                     what was accepted rather than fixed), and report on crosschat
  - If goal not met: write the next action.md, then exit this run
```

Each cycle is written to `logs/cycle-N.md`. **Immutable.**

**Stall cap: 8 cycles.** If cycle 8 ends without the goal met, stop and report why.

**Fail-safe deadline: 2026-10-11 06:00 +0530.** Stop, converged or not, and report where it
stopped on crosschat.

**Work on `feature/46-dream-cycle`**, cut from `main`. Check the branch before writing; a
cycle that wakes elsewhere switches, never commits there. Never merge. Commit, then push,
each cycle (two separate shell invocations).

**Assume a fresh context.** Only these files exist. Read the issue from GitHub before the
diff and before the previous log.

**Never touch the live store from a check.** Scratch under
`C:/Projects/.tmp/second-brain-loop-46/`.

**Report over crosschat** at the end of every cycle, one message, from the maintainer
session: `python -m crosschat send sb-synaptra-maintainer velasari "#46 cycle N: X/11 met, what moved, what is next"`.

**Read the clock rather than assuming it.** `date "+%Y-%m-%d %H:%M %z"`.

**One command per shell invocation.** No `;`, `&&` or `||` chaining.
