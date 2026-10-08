# Overnight queue — 2026-10-08 → 09

The cron reads this file. **Each run: find the first loop below that is not DONE, read
its `loop.md`, and run ONE cycle of it.** If a loop is STALLED, or the fail-safe at
**2026-10-09 07:30 +0530** has passed, delete the cron and report on crosschat to velasari instead.

When every loop is DONE: delete the cron and send velasari one message with the eight
results.

Order is dependency order; do not skip ahead.

| # | Issue | Loop | State |
|---|---|---|---|
| 1 | #38 | `38-clone-projects/iteration-1/loop.md` | DONE — 7/7 in 4 cycles (AC1 SSH half manual-test) |
| 2 | #39 | `39-learn-project-context/iteration-1/loop.md` | in progress — cycle 2 done, 2/6 |
| 3 | #40 | `40-issue-tracker/iteration-1/loop.md` | pending |
| 4 | #41 | `41-monitor-projects/iteration-1/loop.md` | pending |
| 5 | #42 | `42-due-diligence/iteration-1/loop.md` | pending |
| 6 | #43 | `43-follow-project-method/iteration-1/loop.md` | pending |
| 7 | #44 | `44-work-queue/iteration-1/loop.md` | pending |
| 8 | #45 | `45-adopt-hooks/iteration-1/loop.md` | pending |
