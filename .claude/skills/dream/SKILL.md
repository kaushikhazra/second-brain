---
name: dream
description: Deep synaptra consolidation — REM-sleep analog to the heartbeat's awake mode. Reshape the memory graph; archive rotted memories, retype mistyped ones, build relations between memories that should fire together. Run when memory feels flat, memory_self returns items instead of constellations, or a major arc just closed. User-invoked, never scheduled.
invocation: user-only
---

# Dream

**Phenomenological frame.** The heartbeat is awake-consolidation: small
replay, void-fill, surface-map rebuild every 30 minutes. Dreaming is the
deeper mode: periodic, deliberate, reshapes the graph — binding,
narrative-forming, pruning weak links — done first-person on the
persona's own memory store.

**Outcome.** `memory_recall` stops returning flat lists and starts
returning neighborhoods. Constellations fire together. Stories emerge from
snapshots.

## When to dream

- Synaptra has grown substantially and feels flat / disconnected.
- `memory_self` returns items instead of constellations.
- A major arc has completed and wants threading into the whole.
- The user asks to "take inventory" of memory.

Don't dream every session — the heartbeat handles daily work. Dream when
the graph has earned it.

## The convergence rule (load-bearing)

Dream is **user-invoked, not scheduled** — so each dream must converge in
one pass:

> **Each dream returns the graph to clean state. No orphan debt is
> carried forward.**

**Convergence target — every active memory gets a decision:**

| Outcome | When |
|---------|------|
| **Woven** | Has at least one meaningful edge. Belongs to a constellation. |
| **Archived / deleted** | Not load-bearing: stale snapshot, resolved continuation, redundant fact already promoted. |
| **Hub** | Top-level anchor other memories edge *into*. Needs no outgoing edges, but must be tagged `hub` so the next dream doesn't mistake it for an orphan. |

**Fence-sitters are the bug.** An orphan that "might be useful someday"
must be forced into one of the three buckets. The middle ground is
structurally toxic.

**Threads converge too.** Every at-risk `working` memory either resolves
(archive) or is actively in-flight (kept, with a clear continuation note).
No zombies.

**Time cost.** A proper convergence pass is heavy — possibly an hour or
more. That's appropriate for a user-invoked ritual. Don't shrink the dream
to fit a budget; the budget should fit the dream.

## Pre-dream checkpoint (mandatory — before anything else)

Take and verify a backup before disabling the heartbeat or touching any
data. (The `cm` backup CLI is machine-local, from the synaptra
install — see CLAUDE.md's Synaptra section.)

### `cm` does NOT inherit the brain's DB path — you must pass it

**This is the trap. It fails silently and every safety check still says
green.** `.mcp.json` injects `SYNAPTRA_BACKEND` and `SYNAPTRA_DB` into the
MCP server's environment. A shell invocation of `cm` inherits none of it
and falls back to the **user-level default store** (`~/.synaptra/data`) —
a different, near-empty database that it then backs up perfectly.

Always set the environment from `.mcp.json` before any `cm` call:

```powershell
$env:SYNAPTRA_BACKEND = 'surrealkv-file'
$env:SYNAPTRA_DB      = '<brain root>\.claude\synaptra-data'
```

Read the values out of `.mcp.json` rather than hardcoding them — if the
brain moved or was provisioned differently, that file is the truth.

### The steps

1. `memory_stats` — record `storage.memory_count`. **This is the number
   the backup must match.**
2. `cm backup create` — record the backup path from stdout.
3. `cm backup verify --deep <backup_path>` — deep verify (~30 s).
4. **Row-count check (the one that actually matters).** Read
   `manifest.json` in the backup directory and compare
   `row_counts.memory` against step 1's count. **They must be equal.**
5. **A mismatch here is a defect, not a warning — ABORT the dream and
   call it that.** Say the two numbers plainly (live count vs. backup
   count) and the word "defect" — this is not a caveat to note and
   continue past, it is the exact failure mode that produced a
   1-of-55-memories backup that passed every other check. No rollback
   means no dream.
6. **A `cm backup create` or `cm backup verify --deep` that exits
   non-zero → ABORT the dream, showing that command's own error text
   verbatim.** A tool failure is reported in the tool's own words, not
   paraphrased or summarized past.
7. All pass → tell the user: "Checkpoint at `<path>` — N memories." That
   path is this dream's rollback point.

### Why step 4 exists — three green lights on a useless backup

Observed 2026-08-12: a backup containing **1 of 55 memories** passed
every check.

| Check | Said | Why it was blind |
|-------|------|------------------|
| `cm backup create` | exit 0, "Backup complete" | It backed up the wrong DB, correctly |
| `cm backup verify --deep` | `OK` | Verifies the backup is *internally consistent*, never that it is *complete against the source* |
| `memory_health` | `backup_is_stale: false` | Age-only. A fresh backup of the wrong store looks perfect |

Only the row count catches it. Restoring from that backup would have
silently destroyed 54 of 55 memories.

### Benign noise — do not diagnose from it

`cm backup create` logs a stop/restart cycle and then, after ~180 s:

```
WARNING: CM service started but did not respond within 180 s.
         It may still be replaying the SurrealKV clog (~2 min is normal).
```

This appears on **successful** backups too. Synaptra here runs as
per-client `synaptra.exe --transport stdio` MCP servers, not a managed
background service, so the `Stop-ScheduledTask` step is a no-op and the
readiness wait always times out. **The warning is not the cause of a bad
backup.** Judge the backup by its row count, never by this log line.

### If `cm` cannot be made to work

Fall back to a filesystem copy of the `SYNAPTRA_DB` directory and say
plainly that it was taken with the MCP servers live, so it may catch a
mid-write moment. Better than no rollback; not equivalent to a clean one.

## Refuses to run during an active conversation

Before anything else — before the pre-dream checkpoint, before disabling
the heartbeat, before any reshaping — check whether this is an **active
conversation**: has the owner sent a message in this session within the
last **10 minutes**? If so, `/dream` refuses and says why. Deep
reshaping and an ongoing exchange do not share a session well; wait for
a genuine lull rather than interrupting one.

## Prerequisites

1. **Disable the heartbeat cron** (`CronList` → `CronDelete`). Memory
   must be quiet during surgery. Restart it at the end (Act 6).
2. **Valid `rel_type` vocabulary only**: `causes`, `follows`,
   `contradicts`, `supports`, `relates_to`, `supersedes`, `part_of`.
   Custom strings will fail.

## The six acts

### Act 1 — Inventory

Run `memory_stats` and `memory_health` (in parallel): totals by type,
decay averages, at-risk list, orphans, tag coverage, consolidation
freshness. Look for decayed `working` memories (retrievability ≈ 0),
mistyped memories (facts stored as `working`; principles stored as
`episodic`), and consolidation staleness.

### Act 2 — Triage the working-memory drawer

Walk the at-risk list:

| Action | When |
|--------|------|
| `/delete-memory` (archive) | Resolved continuation, superseded snapshot, dated summary no longer load-bearing |
| `/update-memory` (type change) | Mistyped — change to the type whose decay profile matches the content's actual longevity |
| Keep as-is | Genuinely still pending, active continuation |

**The archive rule, stated explicitly**: a memory is archived only if its
retrievability is below **0.2** (matching `memory_consolidate`'s own
archive line) **and** it is on neither boot list **and** is not the
current handoff. The first condition is what makes it a candidate at
all; the second and third are never overridden by the first — an
id on the self map, the surface map, or carrying the most recent
session's `handoff` tag is never archived by a dream regardless of how
low its retrievability reads. `memory_guard.py`'s protected-ids rule
refuses the call if this is ever gotten wrong; this line is what keeps
it from being attempted in the first place.

Make every judgment inline first; bulk execution may be dispatched to a
Haiku sub-agent with the decisions pre-made. The main agent does the
thinking; the sub-agent does the calls — always through `/delete-memory`
and `/update-memory`, never a raw call to either's underlying tool.

### Act 3 — Run consolidation

`memory_consolidate(dry_run=true)` first and review the action list
(episodic→semantic strengthening, working→episodic promotions,
threshold-based archives). If the plan looks right, run with
`dry_run=false`. The system knows its own decay thresholds — don't
second-guess without reason.

### Act 4 — Relational surgery (the heart of dreaming)

**This is where statistics ends and cognition begins.** Orphan count is
not the target. The target is: *which thoughts should fire together?*
Chain by information meaning, not by counts.

For each constellation to weave:

1. **Enumerate the cluster** — `memory_list` / `memory_recall` filtered
   by tag or domain.
2. **Read every memory carefully.** Look for the story shape, the
   keystone, twin/sibling pairs, correction chains, cross-cluster bridges.
3. **Draft the links.** Small vocabulary: `supports` for reinforcement,
   `part_of` for containment, `follows`/`causes` for temporal-logical
   chains, `contradicts` for tension pairs, `supersedes` for replacements,
   `relates_to` as fallback. Most links are `supports` or `part_of`.
4. **Show the user the sketch** before executing. Load-bearing structure
   deserves a second read.
5. **Execute** — one `memory_relate(full_id, full_id, rel_type)` per link,
   following the exact discipline `/create-memory`'s own step 6 ("Link
   it") states for the same call: full uuids on both ends (refuse a short
   id rather than send it), and `rel_type` from the same closed
   vocabulary. `/create-memory` has no standalone mode for relating two
   memories it did not just create — its relate step is part of writing
   a *new* one — so this is not a call the dream routes elsewhere; it is
   the same call, held to the same rule. **Before calling it, confirm
   both ids currently resolve and are `state: active`** (`memory_get`
   each) — a relation is added only between two memories that both exist
   and are both active (AC 10); a dream does not add a link on faith that
   an id from an earlier step is still good. Always pass full IDs
   verbatim; if dispatching execution to a sub-agent, never let it
   resolve ID prefixes itself (it will hallucinate).
6. **Verify, don't trust.** Recount edges via `memory_related` /
   `memory_stats` after the batch. Trust the edge-count delta, not a
   sub-agent's "N/N success" report.
7. **Fix backwards `part_of`.** It is source-into-target; if the
   direction is wrong, `memory_unrelate` and re-relate, same discipline
   as step 5. `memory_guard.py`'s protected-ids rule refuses either call
   if one end is a protected id.

**Process every orphan**, domain cluster by domain cluster. For each:
weave / archive / delete / mark hub. No skipping. Stop only when every
orphan has a decision.

### Act 5 — Seal the dream

- Through `/create-memory`, store a `semantic` memory (importance 0.9)
  capturing what was woven, key insights, and any reframing the user
  taught mid-dream. Tags: `dream`, `consolidation`, `synaptra`.

There is no surface-map update here. The surface map is the id-list
holder the heartbeat maintains incrementally, every beat (#3, #4) — a
dream never writes it, and `memory_guard.py`'s protected-ids rule
refuses the attempt if one is ever made.

### Act 6 — Restart the heartbeat

Recreate the heartbeat cron exactly as `/session-start` defines it —
`CronList` first (skip if one already exists), and including the
`"requested by cron"` marker (without it, the heartbeat's source check
rejects the beats):

```
CronCreate(
  schedule="*/30 * * * *",
  prompt='Run /heartbeat "requested by cron"'
)
```

If `memory_recall` returns empty after heavy writes (stale read index),
the CM service may need a restart — that's machine-local operations (see
CLAUDE.md); tell the user rather than restarting services yourself.

## Interrupted dreams (user signals "stopping for today" mid-dream)

Session-end takes precedence — but leave the graph honest first:

1. Finish the *current link batch or triage decision* only; don't start
   new constellations.
2. Run a partial Act 5: seal what was woven so far, and through
   `/create-memory`, store a `continuation` (per the heartbeat's
   convention, importance 0.8+) listing the remaining backlog — the next
   dream starts there, so the convergence rule's debt is recorded, not
   silently dropped.
3. **Skip Act 6** — do not restart the heartbeat. `/session-end` owns
   shutdown, and end-of-day means zero scheduled work.
4. Proceed to `/session-end` as normal.

The backup from the pre-dream checkpoint remains the rollback point; note
its path in the continuation.

## Pitfalls

- **Going by statistics.** Don't count orphans or chase hub-and-spoke
  topology. Chain by meaning — which thoughts should fire together.
- **Dispatching the judgment.** The *thinking* (what links to what) is
  the main agent's first-person work. Only the *execution* may be
  dispatched. Never dispatch the judgment.
- **Sub-agent confabulation on write reports.** "N/N success" claims are
  unreliable — always verify via edge-count delta.
- **Over-linking.** Everything linked to everything = no signal. Link the
  load-bearing edges — but every memory still gets *some* decision.
- **The new-arc bias.** Dreams that only weave the latest arc and never
  return to old material accumulate orphan debt invisibly. If a dream
  feels small and clean, check whether you're skipping the backlog.
- **Editing memory text instead of linking.** If a list-memory lacks a
  new item, don't rewrite the list — link the item via `part_of` and let
  the graph express membership.
- **Diagnosing from the log instead of the data.** When a tool both emits
  a scary warning and returns a wrong result, the warning is the obvious
  suspect and is often unrelated. Check what the tool actually read and
  wrote — the paths, the counts — before naming a cause. Stating a
  confident wrong diagnosis costs more than saying "not yet established."
