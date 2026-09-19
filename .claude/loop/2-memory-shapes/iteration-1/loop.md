# Loop

```
Goal:                goal.md          (immutable)
Observe rules:       observe.md       (immutable)
Assumptions:         assumption.md
Action:              action.md
Artifact under test: C:/Projects/second-brain/.claude/shared/memory/  and  .claude/skills/{create,read,update,delete}-memory/
Branch:              feature/2-memory-shapes
Issue:               https://github.com/kaushikhazra/second-brain/issues/2

Every 15 minutes, ONE iteration:
  - Action:  work on the skills and the checks, as action.md asks
  - Observe: check against the goal, using observe.md
  - If goal met:     stop the loop, delete the cron, comment on issue #2 with the numbers,
                     and say so on crosschat to velasari
  - If goal not met: write the next action.md, then exit this run

Fail-safe: at 2026-09-19 23:30 +0530, stop and delete the cron, converged or not, and
say on crosschat to velasari where it stopped and why.
```

`goal.md` and `observe.md` do not change. Everything else may, including the assumptions —
if an assumption changes, record it in that cycle's Observe.

Each cycle is written to `logs/cycle-N.md`. **These are immutable — they report the state
at that cycle and are never edited afterwards.**

**The skills are not this folder's artifact.** Skills stay in `.claude/skills/`, the
shared file in `.claude/shared/`, and checks beside the thing they check. This folder
holds the loop's own files and logs, nothing else.

**Work on `feature/2-memory-shapes`.** Cut from `main` at ad3ec00 after PR #9. Check the
branch before writing; a cycle that wakes on `main` must switch, not commit. Commit and
push each cycle.

**Assume a fresh context.** Only these files exist. Read the issue from GitHub before the
diff and before the previous log.

**Run one cycle and exit.** Do not continue into a second cycle in the same run.

**Never touch the live store.** Checks run against a scratch synaptra data directory under
`C:/Projects/.tmp/second-brain-loop-2/`. `.claude/synaptra-data` is the owner's memory.

**Report over crosschat.** At the end of every cycle send one message to `velasari`:
`crosschat send second-brain velasari "<cycle N: criteria met X/27, what moved, what is next>"`.
A blocked cycle says what blocks it on the same channel rather than only in the log.

**Read the clock rather than assuming it.** `date "+%Y-%m-%d %H:%M %z"`.

**First run: on the cron's first fire after 2026-09-19 16:00 +0530. Fail-safe deadline:
2026-09-19 23:30 +0530.** Cycles every 15 minutes, changed from 20 at 16:25 on Kaushik's instruction.
