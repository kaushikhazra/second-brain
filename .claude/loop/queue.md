# Multi-project queue — #38 to #45

The cron reads this file. **Each run: find the first loop below that is not DONE, read
its `loop.md`, and run ONE cycle of it.** If a loop is STALLED, or the fail-safe below
has passed, delete the cron and report on crosschat to velasari instead.

When every loop is DONE: delete the cron and send velasari one message with the eight
results.

Order is dependency order; do not skip ahead.

**Fail-safe: `2026-10-10 07:30 IST`** — Velasari gives the deadline in the start
message, and the session writes it here before the first cycle. Every loop's `loop.md`
uses this one value.

| # | Issue | Loop | State |
|---|---|---|---|
| 1 | #38 | `38-clone-projects/iteration-1/loop.md` | DONE — 7/7 in 4 cycles (AC1 SSH half manual-test) |
| 2 | #39 | `39-learn-project-context/iteration-1/loop.md` | DONE — 6/6 in 4 cycles |
| 3 | #40 | `40-issue-tracker/iteration-1/loop.md` | DONE — 6/6 in 2 cycles |
| 4 | #41 | `41-monitor-projects/iteration-1/loop.md` | DONE — 7/7 in 2 cycles |
| 5 | #42 | `42-due-diligence/iteration-1/loop.md` | DONE — 5/5 in 3 cycles (run 1 cycle 1, run 2 cycles 2–3) |
| 6 | #43 | `43-follow-project-method/iteration-1/loop.md` | DONE — 5/5 with a brain on the final skill text, a removal demo failing for each; regression #38–#42 holds. GitHub issue left open |
| 7 | #44 | `44-work-queue/iteration-1/loop.md` | DONE — 5/5 (script 30/30, brain halves of AC1, 3, 4, 5 pass, demos fail when cut for add, edit, next, boot). Accepted: the view half of AC3 has no failing brain-level demo (the brain reads queue.json itself). GitHub issue left open |
| 8 | #45 | `45-adopt-hooks/iteration-1/loop.md` | DONE — 5/5 (script 23/23; brain and live halves pass, demos fail when cut for all six). GitHub issue left open |

## BUILD-ONLY mode (Kaushik's option B, via velasari, 2026-10-09 ~16:15 IST) — in force

Supersedes the usage paragraph above wherever they differ, and the pause below (resumed).

1. **NO `claude -p` anywhere.** No check that spawns a brain, no removal demo that
   spawns one, no regression pass that spawns one. Spawned sessions drain the allowance.
2. Implement #43's remaining criteria, then #44, then #45, **as written**.
3. Verify with **script checks only**: Python asserts on scripts, files and state. No LLM.
4. A criterion that can only be proven by a brain's behaviour is **behaviour-pending**:
   not counted, listed per issue, waits for the new test method.
5. An issue is **DONE-build** when implemented and its script checks pass. Leave the
   GitHub issue **open**, with a comment listing its behaviour-pending criteria.
6. No product change beyond the issues as written.

Report each issue's DONE-build, and any stop, to velasari. Existing `check_*.py` and
`demo_*` scripts that spawn a brain are not run; leave them in place.

## Brain-run window (Kaushik, via velasari, 2026-10-09 ~20:30 IST)

Build-only mode above is lifted for one window: the behaviour-pending checks are run with
`claude -p`, in this order — #43 AC3/AC5/AC4, #44 brain halves, #45 brain/live halves, one
#38–#42 regression pass — until `~/.claude/rl-status.json` shows `five_hour`
`used_percentage` >= 90, or 20:55 IST, whichever is first; then stop cleanly.

**Window closed 20:54 IST (used 25% of the five-hour allowance).** Not run: the #45 brain halves, the #38–#42 regression, #44 demos view/edit/next/boot, #43 ac4 demo on the current text. Build-only mode resumed; then a second window (2026-10-09 23:17 – 2026-10-10 00:05, one claude -p at a time, 26% used) ran the rest: #45 brain/live halves, the #44 demos, #43 AC4 demo, and the #38–#42 regression — all done, see each loop's `logs/brain-window-*`.

**Checks run sequentially, never in parallel.** One `claude -p` brain live at a time. Let a
run finish before the next starts; do not kill a run unless it is stuck. (Four chains were
live at once at ~20:35 — the first minutes of this window broke this rule.)

## Pause after #43 (Kaushik, via velasari, 2026-10-09) — lifted by the resume above

**Superseded by a pause now (2026-10-09 ~15:00 IST):** cron `79492318` deleted mid-cycle 3
of #43, background checks stopped, state in `43-…/logs/cycle-3.md` and its `action.md`.
The session does nothing until velasari sends the resume; on resume, create the cron again
(`7,22,37,52 * * * *`, same prompt) and run cycle 4 of #43 from its `action.md`.

Original order, still in force once #43 is DONE: after its close regression pass,
CronDelete the cron, mark the #44 row `#44 next, paused for usage reset`, report to
velasari, and **do not start #44** until the resume.

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
Within a cycle, run only the checks the cycle changed — not every check twice.

**From 2026-10-09 (Kaushik, via velasari): the full regression pass — every earlier
issue's checks, #38 up to the loop in hand — runs ONLY when an issue closes**, once, at
the cycle that meets the goal. Not every cycle. Product scope stays as ruled: no product
change mid-run beyond what the issue in hand asks for as written.
