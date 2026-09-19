# Loop

```
Goal:                goal.md          (immutable)
Observe rules:       observe.md       (immutable)
Assumptions:         assumption.md
Action:              action.md
Artifact under test: .claude/skills/session-start/  session-end/  init-brain/  .claude/hooks/memory_guard.py
Branch:              feature/3-boot-lists
Issue:               https://github.com/kaushikhazra/second-brain/issues/3

Every 15 minutes, ONE iteration:
  - Action:  work on the skills and the checks, as action.md asks
  - Observe: check against the goal, using observe.md
  - If goal met:     stop the loop, delete the cron, comment on issue #3 with the numbers,
                     and say so on crosschat to velasari
  - If goal not met: write the next action.md, then exit this run

Fail-safe: at 2026-09-19 23:30 +0530, stop and delete the cron, converged or not, and
say on crosschat to velasari where it stopped and why.
```

`goal.md` and `observe.md` do not change. Everything else may, including the assumptions —
if an assumption changes, record it in that cycle's Observe.

Each cycle is written to `logs/cycle-N.md`. **These are immutable.**

**The skills are not this folder's artifact.** Skills stay in `.claude/skills/`, the hook
in `.claude/hooks/`, checks beside the thing they check. This folder holds the loop's own
files and logs, nothing else.

**Work on `feature/3-boot-lists`.** Cut from `main` at c778024 after PR #10. Check the
branch before writing; a cycle that wakes on `main` must switch, not commit. Commit and
push each cycle.

**Assume a fresh context.** Only these files exist. Read the issue from GitHub before the
diff and before the previous log.

**Run one cycle and exit.**

**Never touch the live store.** Checks run against scratch synaptra data directories under
`C:/Projects/.tmp/second-brain-loop-3/`. `.claude/synaptra-data` is the owner's memory.

**Do not regress #2.** `check_shapes.py` and `check_hooks.py` pass at the end of every
cycle, and no skill outside the four memory skills gains a direct `memory_store`,
`memory_update` or `memory_delete`.

**Report over crosschat.** At the end of every cycle:
`crosschat send second-brain velasari "cycle N: criteria met X/20, what moved, what is next"`.
A blocked cycle says what blocks it on the channel, not only in the log. A judgement call
you are not sure of: say so and proceed, the way #2 did; do not wait.

**Read the clock rather than assuming it.** `date "+%Y-%m-%d %H:%M %z"`.

**First run: now, 2026-09-19 ~19:00 +0530, by hand, then the cron. Fail-safe deadline:
2026-09-19 23:30 +0530.**
