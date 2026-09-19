# Loop

```
Goal:                goal.md          (immutable)
Observe rules:       observe.md       (immutable)
Assumptions:         assumption.md
Action:              action.md
Artifact under test: .claude/skills/heartbeat/  (SKILL.md · observe.md · goal.md · check_heartbeat.py)
Branch:              feature/4-heartbeat
Issue:               https://github.com/kaushikhazra/second-brain/issues/4

Every 15 minutes, ONE iteration:
  - Action:  work on the skill and the checks, as action.md asks
  - Observe: check against the goal, using observe.md
  - If goal met:     stop the loop, delete the cron, comment on issue #4 with the numbers,
                     and say so on crosschat to velasari
  - If goal not met: write the next action.md, then exit this run

Fail-safe: at 2026-09-19 23:59 +0530, stop and delete the cron, converged or not, and
say on crosschat to velasari where it stopped and why.
```

`goal.md` and `observe.md` in THIS folder do not change; they are the loop's goal and
observe rules. The heartbeat's own `observe.md` and `goal.md` under `.claude/skills/heartbeat/`
are the artifact, and they are what the loop writes. Do not confuse the two pairs.

Each cycle is written to `logs/cycle-N.md`. **These are immutable.**

**The skill is not this folder's artifact.** It stays in `.claude/skills/heartbeat/`, checks
beside it. This folder holds the loop's own files and logs, nothing else.

**Work on `feature/4-heartbeat`.** Cut from `main` at 6e060f1 after PR #11. Check the
branch before writing; a cycle that wakes on `main` must switch, not commit. Commit and
push each cycle.

**Assume a fresh context.** Only these files exist. Read the issue from GitHub before the
diff and before the previous log.

**Run one cycle and exit.**

**Never touch the live store.** Scratch stores under `C:/Projects/.tmp/second-brain-loop-4/`.

**Do not regress #2 or #3.** `check_shapes.py`, `check_hooks.py`, `check_session_start.py`
pass at the end of every cycle.

**Report over crosschat.** At the end of every cycle:
`crosschat send second-brain velasari "cycle N: criteria met X/20, what moved, what is next"`.
A blocked cycle says what blocks it on the channel. A judgement call you are not sure of:
say so and proceed.

**Read the clock rather than assuming it.** `date "+%Y-%m-%d %H:%M %z"`.

**First run: now, 2026-09-19 ~20:10 +0530, by hand, then the cron. Fail-safe deadline:
2026-09-19 23:59 +0530.**
