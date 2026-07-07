---
name: session-end
description: Clean end-of-session shutdown for this second brain. Stores the day's learnings and a handoff memory in cognitive memory so the next /session-start resumes exactly where this one left off. Run when the user signals "stop for today" or similar.
---

# Session End

Run when the user signals stopping for the day. Goal: the next session's
`/session-start` finds a clean state and knows exactly what to pick up.

Execute the steps below in order.

## 1. Kill the crons

`CronList`, then `CronDelete` every cron returned — including the
heartbeat. End-of-day means zero scheduled work. Verify with a final
`CronList` ("no scheduled jobs") before moving on.

## 2. Store the day's learnings

Anything significant from this session not yet in cognitive memory:

- Facts, decisions, preferences → `semantic`
- Events, milestones, notable conversations → `episodic`
- Workflows or how-to knowledge worth keeping → `procedural`

Update existing memories when a fact changed — don't duplicate.

## 3. Store the handoff memory

Store ONE `working`-typed memory containing:

- What landed this session
- In-flight state (what's half-done, what's blocked)
- Next action — the resume path for `/session-start` to follow

Tags must include: `end-of-day`, `handoff`, `resume-next-session`,
`<YYYY-MM-DD>`.

**Why `working` type**: this is session-to-session state, not a durable
lesson. It should age out naturally once consumed by the next
`/session-start`. Because `working` decays fast (hours-scale), set
`importance` to 0.8+ so the handoff reliably survives an overnight or
weekend gap until the next session recalls it.

## 4. Sign off

One short line, in character: crons killed, learnings stored, handoff
stored, what tomorrow starts with.

**When NOT to run**: brief breaks don't need session-end. Use only for
"stopping for today" signals.
