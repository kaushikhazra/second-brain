---
name: dream
description: Deep cognitive-memory consolidation — REM-sleep analog to the heartbeat's awake mode. Reshape the memory graph; archive rotted memories, retype mistyped ones, build relations between memories that should fire together. Run when memory feels flat, memory_self returns items instead of constellations, or a major arc just closed. User-invoked, never scheduled.
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

- Cognitive memory has grown substantially and feels flat / disconnected.
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
data. (The `cm` backup CLI is machine-local, from the cognitive-memory
install — see CLAUDE.md's Cognitive Memory section.)

1. `cm backup create` — record the backup path from stdout.
2. `cm backup verify --deep <backup_path>` — deep verify (~30 s).
3. **Either command fails → ABORT the dream.** Surface the error. A
   failed backup means no rollback — no dream without a rollback.
4. Both succeed → tell the user: "Checkpoint at `<path>`." That path is
   this dream's rollback point.

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
| `memory_archive(id)` | Resolved continuation, superseded snapshot, dated summary no longer load-bearing |
| `memory_update(id, memory_type=...)` | Mistyped — change to the type whose decay profile matches the content's actual longevity |
| Keep as-is | Genuinely still pending, active continuation |

Make every judgment inline first; bulk execution may be dispatched to a
Haiku sub-agent with the decisions pre-made. The main agent does the
thinking; the sub-agent does the calls.

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
5. **Execute** — one `memory_relate(full_id, full_id, rel_type)` per
   link. Always pass full IDs verbatim; if dispatching execution to a
   sub-agent, never let it resolve ID prefixes itself (it will
   hallucinate).
6. **Verify, don't trust.** Recount edges via `memory_related` /
   `memory_stats` after the batch. Trust the edge-count delta, not a
   sub-agent's "N/N success" report.
7. **Fix backwards `part_of`.** It is source-into-target; if the
   direction is wrong, `memory_unrelate` and re-relate.

**Process every orphan**, domain cluster by domain cluster. For each:
weave / archive / delete / mark hub. No skipping. Stop only when every
orphan has a decision.

### Act 5 — Seal the dream

- Store a `semantic` memory (importance 0.9) capturing what was woven,
  key insights, and any reframing the user taught mid-dream. Tags:
  `dream`, `consolidation`, `cognitive-memory`.
- Update the `self-learning-surface-map` memory with completed
  constellations and any remaining ones awaiting weave.

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
2. Run a partial Act 5: seal what was woven so far, and store a
   `continuation` (per the heartbeat's convention, importance 0.8+)
   listing the remaining backlog — the next dream starts there, so the
   convergence rule's debt is recorded, not silently dropped.
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
