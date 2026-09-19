---
name: heartbeat
description: Cron-fired consolidation cycle. Observe, act, repeat until the session ends. Silent unless something can't wait.
invocation: cron-only
output: silent
---

# Heartbeat

A loop. The cron fires it at the configured interval; it runs one cycle and stops.
The loop ends only when the session ends.

Order is **observe → act**.

## Files

| file | holds |
|---|---|
| `observe.md` | what to watch for |
| `goal.md` | what to do about each thing observed |

Sections in the two files pair by `id`. An id in one file with no match in the other
is a gap — the beat reports it, it does not act on it.

**A beat never edits `observe.md` or `goal.md`.** If a cycle concludes one should
change, store the proposal as a memory and stop — the owner rules on it later.

## Steps

1. Get the local timestamp.
2. Use `observe.md` to see what needs to be observed, section by section.
3. If nothing was observed anywhere, stop — **except** `surface-map`'s exit walk
   (`observe.md` § `surface-map`), which still runs on an otherwise-empty window.
4. For everything observed, reference `goal.md` and perform the matching action.

The window is everything since the previous beat in this session, or since session
start if this is the first beat. Previous beats are visible in context — that is also
where the quiet-beat count lives; nothing is written to a file for it.

## Invocation source check

The cron prompt carries the words `requested by cron`. If that marker is absent, this
is a manual invocation — run normally and say so, rather than treating the marker's
absence as an error.

## Output

Silent by default — the beat runs and reports nothing.

Break silence only when what was observed cannot wait for the owner to ask:

- something is failing, or about to
- something is time-bound and the window is closing
- a message arrived from outside this session and is addressed to the owner

The first two are the brain speaking — do not repeat one the owner has not answered.
The third is the world speaking through the brain and surfaces regardless of that.

## Failure

**Synaptra unreachable.** A call fails because the store can't be reached — say so
once and stop the beat. No retry. This is the first silence exception above
("something is failing"), not a fourth case.

**No double-run.** Each cron fire is its own fresh invocation of this skill; there is
no persistent loop process for a slow beat to overrun. "Not run twice" is a property
of that invocation model, not a lock this skill has to track.
