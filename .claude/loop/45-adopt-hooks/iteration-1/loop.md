# Loop

```
Goal:                goal.md          (immutable)
Observe rules:       observe.md       (immutable)
Assumptions:         assumption.md + ../../multi-project-assumptions.md
Action:              action.md
Artifact under test: the brain under src/, and its checks under checks/multi-project/
Branch:              feature/multi-project
Issue:               https://github.com/kaushikhazra/second-brain/issues/45

ONE cycle per run:
  - Action:  do what action.md asks
  - Observe: check against the goal, using observe.md
  - If goal met:     comment on issue #45 with the numbers (criteria met, UI-pending
                     named, checks that prove each), mark this loop DONE in
                     ../../queue.md, and report on crosschat to velasari
  - If goal not met: write the next action.md, then exit this run
```

Each cycle is written to `logs/cycle-N.md`. **Immutable** — never edited afterwards.

**Stall cap: 8 cycles.** If cycle 8 ends without the goal met, mark this loop
STALLED in `../../queue.md`, report on crosschat, and stop the whole run (the issues
after this one build on it).

**Fail-safe: the deadline in `../../queue.md`**, stop and delete the cron, converged or not, mark this loop
in `../../queue.md` with where it stopped, and report on crosschat.

**Work on `feature/multi-project`.** Check the branch before writing; a cycle that wakes elsewhere
switches, never commits there. Commit and push each cycle.

**Assume a fresh context.** Only these files exist.

**Run one cycle and exit.**

**Report over crosschat** at the end of every cycle, one message:
`crosschat send second-brain velasari "#45 cycle N: X/5 met, what moved, what is next"`.

**Read the clock rather than assuming it.** `date "+%Y-%m-%d %H:%M %z"`.

**One command per shell invocation.** No `;`, `&&` or `||` chaining. Destructive
commands take absolute paths.
