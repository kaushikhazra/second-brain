# Loop

```
Goal:                goal.md          (immutable)
Observe rules:       observe.md       (immutable)
Assumptions:         assumption.md
Action:              action.md
Document under test: C:/Projects/second-brain (branch feature/47-command-guard): src/.claude/hooks/command_guard.*, guard/, src/.claude/settings.json

Every 24 minutes, ONE iteration:
  - Action:  work on the artifact, as action.md asks
  - Observe: check it against the goal, using observe.md
  - If goal met:     stop the loop and delete the cron
  - If goal not met: write the next action.md, then exit this run

Fail-safe: at 2026-10-16T09:30+05:30, stop and delete the cron, converged or not.
```

`goal.md` and `observe.md` do not change. Everything else may, including the assumptions — if an assumption changes, record it in that cycle's Observe.

Each cycle is written to `logs/cycle-N.md`. **These are immutable — they report the state at that cycle and are never edited afterwards.**

The artifact already existed at the start, so **cycle 1 reads it and records where it stands. It does not write.** After that the loop edits the artifact; it never regenerates it.

Each cycle ends by reporting to `velasari` over crosschat when a milestone was hit, or when blocked or finished: `python -m crosschat send sb-synaptra-maintainer velasari "<message>"`.

**First run: 2026-10-15T23:55+05:30. Fail-safe deadline: 2026-10-16T09:30+05:30.**
