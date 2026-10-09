# Multi-project queue — #38 to #45

The cron reads this file. **Each run: find the first loop below that is not DONE, read
its `loop.md`, and run ONE cycle of it.** If a loop is STALLED, or the fail-safe below
has passed, delete the cron and report on crosschat to velasari instead.

When every loop is DONE: delete the cron and send velasari one message with the eight
results.

Order is dependency order; do not skip ahead.

**Fail-safe: `<set when the run starts>`** — Velasari gives the deadline in the start
message, and the session writes it here before the first cycle. Every loop's `loop.md`
uses this one value.

| # | Issue | Loop | State |
|---|---|---|---|
| 1 | #38 | `38-clone-projects/iteration-1/loop.md` | DONE — 7/7 in 4 cycles (AC1 SSH half manual-test) |
| 2 | #39 | `39-learn-project-context/iteration-1/loop.md` | DONE — 6/6 in 4 cycles |
| 3 | #40 | `40-issue-tracker/iteration-1/loop.md` | DONE — 6/6 in 2 cycles |
| 4 | #41 | `41-monitor-projects/iteration-1/loop.md` | DONE — 7/7 in 2 cycles |
| 5 | #42 | `42-due-diligence/iteration-1/loop.md` | in progress — cycle 1 done, 0/5 counted (AC1, 2, 3a pass) |
| 6 | #43 | `43-follow-project-method/iteration-1/loop.md` | pending |
| 7 | #44 | `44-work-queue/iteration-1/loop.md` | pending |
| 8 | #45 | `45-adopt-hooks/iteration-1/loop.md` | pending |

## Resuming after a stop

Run 1 (8→9 Oct) stopped at ~02:45 IST on the account usage limit, not on a stall.
Nothing is lost: every cycle was committed and pushed.

**#42 picks up at cycle 2.** Its first moves, from the stop report:
1. `python checks/multi-project/check_diligence.py --all` fresh, to see where it stands.
2. Removal demos for the criteria that pass (AC1, 2, 3a): each check must fail with the
   behaviour cut. Cut so the brain cannot repair itself — keep the script's answers
   intact (the #40 lesson).
3. Regressions for #38–#41 as every cycle.

**Usage.** Run 1 spent a night's allowance on four issues; most of it went on
`claude -p` calls inside checks. The session now runs on Sonnet (`.claude/settings.json`).
Within a cycle, run only the checks the cycle changed plus one full regression pass —
not every check twice.
