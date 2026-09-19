# Loop

```
Goal:                goal.md          (immutable)
Observe rules:       observe.md       (immutable)
Assumptions:         assumption.md
Action:              action.md
Artifact under test: .claude/skills/news/ · .claude/shared/activation.py (one entry) · session-start (one line) · news-keywords.txt
Branch:              feature/7-news
Issue:               https://github.com/kaushikhazra/second-brain/issues/7

Every 15 minutes, ONE iteration:
  - Action:  work on the skill and the checks, as action.md asks
  - Observe: check against the goal, using observe.md
  - If goal met:     stop the loop, delete the cron, comment on issue #7 with the numbers,
                     and say so on crosschat to velasari
  - If goal not met: write the next action.md, then exit this run

Fail-safe: at 2026-09-20 06:00 +0530, stop and delete the cron, converged or not, and
say on crosschat to velasari where it stopped and why.
```

`goal.md` and `observe.md` in this folder do not change. Each cycle is written to
`logs/cycle-N.md`, immutable.

**The skill is not this folder's artifact.** It stays in `.claude/skills/news/`, checks
beside it.

**Work on `feature/7-news`.** Cut from `main` after PR #15. Check the branch before
writing; a cycle that wakes on `main` must switch, not commit. Commit and push each cycle.

**Assume a fresh context.** Only these files exist. Read the issue from GitHub before the
diff and before the previous log.

**Run one cycle and exit.**

**Never touch the live store, the live activation record, or the live `reading-list.md`
from a check.** Scratch under `C:/Projects/.tmp/second-brain-loop-7/`. A headless proof
that needs YouTube keys uses placeholder keys in a scratch `.env` and asserts the named
failure, never the owner's real keys.

**Do not regress #2 to #6 or #8.** The full regression line, eight scripts, passes at the
end of every cycle.

**Report over crosschat.** At the end of every cycle:
`crosschat send second-brain velasari "cycle N: criteria met X/19, what moved, what is next"`.
A blocked cycle says what blocks it on the channel. A judgement call you are not sure of:
say so and proceed.

**Read the clock rather than assuming it.** `date "+%Y-%m-%d %H:%M %z"`.

**First run: now, 2026-09-20 ~01:05 +0530, by hand, then the cron. Fail-safe deadline:
2026-09-20 06:00 +0530.**
