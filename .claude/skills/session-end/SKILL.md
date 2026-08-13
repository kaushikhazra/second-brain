---
name: session-end
description: Clean end-of-session shutdown for this second brain. Stores the day's learnings and a handoff memory in Synaptra so the next /session-start resumes exactly where this one left off. Run when the user signals "stop for today" or similar.
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

Anything significant from this session not yet in Synaptra:

- Facts, decisions, preferences → `semantic`
- Events, milestones, notable conversations → `episodic`
- Workflows or how-to knowledge worth keeping → `procedural`

Update existing memories when a fact changed — don't duplicate.

## 3. Store the handoff memory

Store ONE `episodic`-typed memory containing:

- What landed this session
- In-flight state (what's half-done, what's blocked)
- Next action — the resume path for `/session-start` to follow

Tags must include: `end-of-day`, `handoff`, `resume-next-session`,
`<YYYY-MM-DD>`.

**Why `episodic` and NOT `working`**: this is session-to-session state
rather than a durable lesson, so `working` looks right — and it is wrong.
`working` decays hours-scale. A handoff is stored at end of day and then
not touched until the next session opens it, which is exactly the access
pattern that collapses retrievability: **R ≈ 0.06 within a day** on
measured data. Anything below 0.2 is archived by `memory_consolidate` on
sight. Over a weekend the handoff is gone before it is ever read.

**`importance` does not protect it.** Importance and retrievability are
independent — on 2026-08-12 a consolidation dry run proposed archiving
five live threads sitting at importance 0.80–0.85. Do not rely on a high
importance value to keep anything alive.

Set `importance` to 0.8+ anyway (it governs ranking, which matters for
recall), but the type is what makes the handoff survive. `episodic`
decays days-scale and still ages out naturally once consumed.

## 4. Sign off

One short line, in character: crons killed, learnings stored, handoff
stored, what tomorrow starts with.

**When NOT to run**: brief breaks don't need session-end. Use only for
"stopping for today" signals.
