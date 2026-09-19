# Loop

```
Goal:                goal.md          (immutable)
Observe rules:       observe.md       (immutable)
Assumptions:         assumption.md
Action:              action.md
Artifact under test: .claude/skills/curiosity/ · .claude/shared/activation.py · the activation step in session-start · heartbeat/goal.md § quiet-cycles (one sentence)
Branch:              feature/6-curiosity
Issue:               https://github.com/kaushikhazra/second-brain/issues/6

Every 15 minutes, ONE iteration:
  - Action:  work on the skill and the checks, as action.md asks
  - Observe: check against the goal, using observe.md
  - If goal met:     stop the loop, delete the cron, comment on issue #6 with the numbers,
                     and say so on crosschat to velasari
  - If goal not met: write the next action.md, then exit this run

Fail-safe: at 2026-09-20 06:00 +0530, stop and delete the cron, converged or not, and
say on crosschat to velasari where it stopped and why.
```

`goal.md` and `observe.md` in this folder do not change. Each cycle is written to
`logs/cycle-N.md`, immutable.

**The skill is not this folder's artifact.** It stays in `.claude/skills/curiosity/`,
checks beside it.

**Work on `feature/6-curiosity`.** Cut from `main` after PR #14. Check the branch before
writing; a cycle that wakes on `main` must switch, not commit. Commit and push each cycle.

**Assume a fresh context.** Only these files exist. Read the issue from GitHub before the
diff and before the previous log.

**Run one cycle and exit.**

**Never touch the live store, and never write the live `.claude/activations.json` or the
live `curiosity/` folder from a check.** Scratch under `C:/Projects/.tmp/second-brain-loop-6/`.

**Do not regress #2 to #5 or #8.** The full regression line passes at the end of every cycle.

**Report over crosschat.** At the end of every cycle:
`crosschat send second-brain velasari "cycle N: criteria met X/20, what moved, what is next"`.
A blocked cycle says what blocks it on the channel. A judgement call you are not sure of:
say so and proceed.

**Read the clock rather than assuming it.** `date "+%Y-%m-%d %H:%M %z"`.

**First run: now, 2026-09-19 ~23:55 +0530, by hand, then the cron. Fail-safe deadline:
2026-09-20 06:00 +0530.**
