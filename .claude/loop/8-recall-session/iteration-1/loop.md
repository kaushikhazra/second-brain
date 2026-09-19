# Loop

```
Goal:                goal.md          (immutable)
Observe rules:       observe.md       (immutable)
Assumptions:         assumption.md
Action:              action.md
Artifact under test: .claude/skills/recall-session/  (SKILL.md · tools/search.py · check_recall_session.py)
Branch:              feature/8-recall-session
Issue:               https://github.com/kaushikhazra/second-brain/issues/8

Every 15 minutes, ONE iteration:
  - Action:  work on the skill and the checks, as action.md asks
  - Observe: check against the goal, using observe.md
  - If goal met:     stop the loop, delete the cron, comment on issue #8 with the numbers,
                     and say so on crosschat to velasari
  - If goal not met: write the next action.md, then exit this run

Fail-safe: at 2026-09-20 06:00 +0530, stop and delete the cron, converged or not, and
say on crosschat to velasari where it stopped and why.
```

`goal.md` and `observe.md` in this folder do not change. Each cycle is written to
`logs/cycle-N.md`, immutable.

**The skill is not this folder's artifact.** It stays in `.claude/skills/recall-session/`,
checks beside it.

**Work on `feature/8-recall-session`.** Cut from `main` after PR #13. Check the branch
before writing; a cycle that wakes on `main` must switch, not commit. Commit and push
each cycle.

**Assume a fresh context.** Only these files exist. Read the issue from GitHub before the
diff and before the previous log.

**Run one cycle and exit.**

**Never touch the live transcripts or the live store.** Scratch under
`C:/Projects/.tmp/second-brain-loop-8/`.

**Do not regress #2 to #5.** The full regression line passes at the end of every cycle.

**Report over crosschat.** At the end of every cycle:
`crosschat send second-brain velasari "cycle N: criteria met X/12, what moved, what is next"`.
A blocked cycle says what blocks it on the channel. A judgement call you are not sure of:
say so and proceed.

**Read the clock rather than assuming it.** `date "+%Y-%m-%d %H:%M %z"`.

**First run: now, 2026-09-19 ~23:40 +0530, by hand, then the cron. Fail-safe deadline:
2026-09-20 06:00 +0530.**
