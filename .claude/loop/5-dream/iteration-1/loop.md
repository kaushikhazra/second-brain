# Loop

```
Goal:                goal.md          (immutable)
Observe rules:       observe.md       (immutable)
Assumptions:         assumption.md
Action:              action.md
Artifact under test: .claude/skills/dream/  ·  .claude/hooks/memory_guard.py  ·  the protected-ids write in session-start
Branch:              feature/5-dream
Issue:               https://github.com/kaushikhazra/second-brain/issues/5

Every 15 minutes, ONE iteration:
  - Action:  work on the skill and the checks, as action.md asks
  - Observe: check against the goal, using observe.md
  - If goal met:     stop the loop, delete the cron, comment on issue #5 with the numbers,
                     and say so on crosschat to velasari
  - If goal not met: write the next action.md, then exit this run

Fail-safe: at 2026-09-20 02:00 +0530, stop and delete the cron, converged or not, and
say on crosschat to velasari where it stopped and why.
```

`goal.md` and `observe.md` in this folder do not change. Each cycle is written to
`logs/cycle-N.md`, immutable.

**The skill is not this folder's artifact.** It stays in `.claude/skills/dream/`, the hook
in `.claude/hooks/`, checks beside the thing they check.

**Work on `feature/5-dream`.** Cut from `main` after PR #12. Check the branch before
writing; a cycle that wakes on `main` must switch, not commit. Commit and push each cycle.

**Assume a fresh context.** Only these files exist. Read the issue from GitHub before the
diff and before the previous log.

**Run one cycle and exit.**

**Never touch the live store, and never run a real dream on it.** Every dream exercised
by a check runs against a scratch store under `C:/Projects/.tmp/second-brain-loop-5/`,
including its backup.

**Do not regress #2, #3 or #4.** The full regression line passes at the end of every cycle.

**Report over crosschat.** At the end of every cycle:
`crosschat send second-brain velasari "cycle N: criteria met X/17, what moved, what is next"`.
A blocked cycle says what blocks it on the channel. A judgement call you are not sure of:
say so and proceed.

**Read the clock rather than assuming it.** `date "+%Y-%m-%d %H:%M %z"`.

**First run: now, 2026-09-19 ~22:30 +0530, by hand, then the cron. Fail-safe deadline:
2026-09-20 02:00 +0530.**
