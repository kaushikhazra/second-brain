# Loop

```
Goal:                goal.md          (immutable)
Observe rules:       observe.md       (immutable)
Assumptions:         assumption.md
Action:              action.md
Artifact under test: .claude/shared/scratch_brain.py  (phase 1)
                     .claude/skills/update/           (phases 2+, not yet created)
Branch:              feature/24-recalibration
Issue:               https://github.com/kaushikhazra/second-brain/issues/24

One cycle:
  - Action:  do what action.md asks
  - Observe: check against the goal, using observe.md
  - If goal met:     stop, comment on issue #24 with the numbers, say so on crosschat
  - If goal not met: write the next action.md, log the cycle, and exit
```

**Driven by velasari over crosschat, not by a cron.** This loop's cadence is the
orchestrator's messages; there is no scheduler entry to create or delete. Kaushik
verifies manually at the end. The fail-safe is therefore velasari's to call, not a
wall-clock deadline in this file — a cycle that finishes reports and stops rather than
scheduling itself.

`goal.md` and `observe.md` in this folder do not change. Each cycle is written to
`logs/cycle-N.md`, immutable.

**The skill is not this folder's artifact.** Shared code stays in `.claude/shared/`,
skills in `.claude/skills/`, checks beside what they check.

**Work on `feature/24-recalibration`.** Cut from `main` at 364834e. Check the branch
before writing; a cycle that wakes on `main` must switch, not commit. Commit and push
each cycle.

**Assume a fresh context.** Only these files exist. Read the issue from GitHub before
the diff and before the previous log.

**Run one cycle and exit.**

**Never touch the live store.** Scratch under `C:/Projects/.tmp/second-brain-loop-24/`.
Never copy a real memory store into the repo or into a fixture.
