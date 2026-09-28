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
`CronList` and **report the count it returns** (should be zero) — "crons
killed" is a claim; the final `CronList`'s own count is what proves it
(AC 12).

## 2. Store the day's learnings

Anything significant from this session not yet in Synaptra:

- Facts, decisions, preferences → `semantic`
- Events, milestones, notable conversations → `episodic`
- Workflows or how-to knowledge worth keeping → `procedural`

Update existing memories when a fact changed — don't duplicate.

## 3. Store the handoff memory

Store ONE `episodic`-typed memory via `/create-memory` (route through the
skill, never a raw store call) containing:

- What landed this session
- In-flight state (what's half-done, what's blocked)
- Next action — the resume path for `/session-start` to follow

Tags must include: `end-of-day`, `handoff`, `resume-next-session`,
`<YYYY-MM-DD>` (AC 8).

⛔ **Read it back after storing.** If it landed as `episodic`, done. If it
landed as `working` instead — `/create-memory`'s own verification step
should already have caught and corrected this, but check again here,
because this is the one memory in the whole brain that must never decay
on the hours-scale `working` uses: retype it with `cm update <id> --type episodic`,
then read it back a **second time** to confirm the correction actually
landed (AC 9). Don't assume the retype worked from its return value —
that is exactly the failure `/create-memory`'s own verify step exists to
prevent, and it applies here too.

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

## 4. Run `verify_memory.py` — both halves

This step is **read-only**: it fetches and checks, it never writes anything
back to either boot list (AC 20 — the surface map is the heartbeat's to
maintain, not this skill's).

1. Fetch active memories: `memory_list(state="active")`.
2. Find the `self-map` and `surface-map` holders in that result (same tag
   filter `/session-start`'s step 3 already uses — don't re-derive it).
   For every id listed in either holder's content, `memory_get` it and
   collect the result into a `resolved` map: `{"<id>": <memory_get result>
   | null}`.
3. Write `{"memories": <the active list>, "resolved": <that map>}` to a
   temp JSON file, then run
   `python .claude/skills/session-end/verify_memory.py <that file>`.
4. **Print its full result** — both the conformance scan (a store whose
   `source` doesn't start with `create-memory:`) and the two-list findings
   (each list present exactly once, its count, every id resolving) — per
   AC 13's literal text, not a summary of one half.

⛔ **Nothing here blocks sign-off, and nothing here blocks step 3.** Step 3
(the handoff) already ran and already landed before this step starts —
a failed verify is reported, never a reason to undo or withhold a store
that already happened (AC 14). Report every finding by id; none of them
get buried in a log the user never reads.

## 5. Sign off

One short line, in character: cron list count (confirming zero), learnings
stored, handoff stored (and retyped, if that happened), `verify_memory.py`'s
findings if any, what tomorrow starts with.

**When NOT to run**: brief breaks don't need session-end. Use only for
"stopping for today" signals.
