# Loop

```
Goal:                goal.md          (immutable)
Observe rules:       observe.md       (immutable)
Assumptions:         assumption.md
Action:              action.md
Artifact under test: the archive a user unpacks, measured against the v1.0.1 tag
Branch:              feature/25-src-split
Issue:               https://github.com/kaushikhazra/second-brain/issues/25

Every 30 minutes, ONE iteration:
  - Action:  do what action.md asks
  - Observe: check against the goal, using observe.md
  - If goal met:     stop the loop, delete the cron, comment on issue #25 with the
                     numbers, and say so on crosschat to velasari
  - If goal not met: write the next action.md, then exit this run

Fail-safe: at 2026-09-29 00:30 +0530, stop and delete the cron, converged or not, and
say on crosschat to velasari where it stopped and why.
```

**Thirty minutes, not fifteen.** A cycle here moves files and then sweeps for path
references across untracked, hidden and binary files. Fifteen minutes buys a cycle that
moves without sweeping, which is the one failure this loop cannot afford.

`goal.md` and `observe.md` do not change. Everything else may, including the assumptions —
if an assumption changes, record it in that cycle's log.

Each cycle is written to `logs/cycle-N.md`. **These are immutable — they report the state
at that cycle and are never edited afterwards.**

**Work on `feature/25-src-split`.** Cut from `main` at parity with `origin/main`. Check
the branch before writing; a cycle that wakes on `main` must switch, not commit. Commit
and push each cycle.

**Assume a fresh context.** Only these files exist. Read the issue from GitHub before the
diff and before the previous log.

**Run one cycle and exit.** Do not continue into a second cycle in the same run.

## ⛔ Stop rather than guess

**Anything in `assumption.md` § Unsettled is Kaushik's to rule, not the loop's.** A cycle
that reaches one of them stops, says so on crosschat, and exits. It does not pick the
likelier answer and carry on.

⚠ He ruled this work should be done *interactively* (CM `12b4a0fa`) before agreeing to
run it as a loop. The loop inherits that: it does the legwork and hands back the
decisions.

## ⛔ Never run `build-dist.py` while `VERSION` reads 1.0.1

It opens by unlinking `dist/second-brain-<VERSION>.zip`, `dist/` is untracked, and
criterion 16 forbids bumping `VERSION`. Compare tree-ishes with
`.claude/shared/check_artifact_unmoved.py` instead. A backup of the six shipped zips is
at `C:/Projects/.tmp/second-brain-dist-reference/`.

**Never touch the live store.** `.claude/synaptra-data` is the owner's memory. Scratch
trees live under `C:/Projects/.tmp/second-brain-loop-25/`, never in the repo and never in
a system temp folder.

**Report over crosschat.** At the end of every cycle send one message to `velasari`:
`crosschat send second-brain velasari "<cycle N: criteria met X/30, what moved, what is next>"`.
A blocked cycle says what blocks it on the same channel rather than only in the log.

**Read the clock rather than assuming it.** `date "+%Y-%m-%d %H:%M %z"`.

**One command per shell invocation.** No `;`, `&&` or `||` chaining. Destructive commands
take absolute paths.
