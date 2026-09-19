# Cycle 1

**Time:** 2026-09-19 15:5x +0530 (read via `date`)
**Branch:** `feature/2-memory-shapes` (confirmed via `git branch --show-current`)

## Baseline (before any changes)

**AC 23 grep** — `grep -rlE "memory_store|memory_update|memory_delete" .claude/skills`:

```
.claude/skills/dream/SKILL.md
.claude/skills/heartbeat/SKILL.md
```

Matches loop.md's prediction exactly.

**Skills present:**

```
agent-creator
dream
heartbeat
init-brain
local-agent
session-end
session-start
```

None of the four memory skills exist yet.

**`cm --help`:**

```
Usage: cm [OPTIONS] COMMAND [ARGS]...

  Synaptra CLI -- browse, search, and manage memories.

Options:
  --url TEXT  Server URL (default: http://127.0.0.1:8050/mcp, env: SYNAPTRA_URL)
  --json      Output raw JSON
  --version   Show the version and exit.
  --help      Show this message and exit.

Commands:
  archive      Archive one or more memories, or all below a...
  backup       Backup and restore CM memory data.
  config       View or set configuration.
  consolidate  Trigger the consolidation pipeline.
  delete       Permanently delete one or more memories.
  get          Get a specific memory by ID.
  list         List memories with optional filters.
  recall       Search memories with multi-strategy retrieval.
  relate       Create a relationship between two memories.
  related      View memories related to a given memory.
  restore      Restore one or more archived memories.
  stats        View memory statistics.
  store        Store a new memory.
  unrelate     Remove a relationship between two memories.
  update       Update a memory's content or metadata.
```

`cm update --help` confirms `--type TEXT` — "New memory type" — is how a type is
changed via the CLI, per assumption.md. `memory_update` (the MCP tool) has no
type argument, confirming it ignores `memory_type`.

## Criteria read from GitHub (issue #2), before the diff

27 acceptance criteria confirmed as written in `.claude/loop/2-memory-shapes/iteration-1/goal.md`'s
source issue. Full text pulled via `gh issue view 2 -R kaushikhazra/second-brain`.

**Note on shape names:** the issue's four shapes are `fact`, `learning`, `persona`,
`person-model`, matching Velasari's source tree's shape names exactly (`boundary` is
a node *inside* the `learning` constellation, not a fifth shape).

## Assumption that changed — verified against synaptra 2.0.0, not assumed

`assumption.md` and Velasari's shapes file both state: *"`memory_store` treats
`memory_type` as a HINT and reclassifies from content"* and *"`memory_update` ignores
`memory_type` entirely."* Read the installed engine (`synaptra/engine.py`, package
version `2.0.0`) instead of trusting that:

- `store_memory`: `if memory_type: mem_type = MemoryType(memory_type)` — an **explicit**
  type is honored as given. `classify(content, source)` only runs when `type` is
  **omitted**. So "hint, always reclassified" is not what this version does.
- `update_memory`: `if memory_type is not None: fields["memory_type"] = MemoryType(memory_type)`
  — the type argument **is applied**, not ignored.

This does not break anything already written: `create-memory` still verifies id+type
after every store (defensive, and correct for the omitted-type path), and still routes
type corrections through `cm update <id> --type` rather than `memory_update`'s type
argument — issue #2's own AC 19 asks for the `cm` path specifically, and that path
still works regardless of whether `memory_update` would also work now. Recorded here,
not silently reconciled, per loop.md: assumptions may change; say so when they do.
The shapes file's "Synaptra specifics" section states the verified behaviour, and
flags it as version-specific rather than a synaptra-wide guarantee.

## What landed

1. **`.claude/shared/memory/memory-shapes.md`** — written for a second brain from
   Velasari's `C:/Projects/ai-persona/Velasari/.claude/shared/memory/memory-shapes.md`.
   Same four shapes, same fork, same create/read/update/delete structure per shape.
   Stripped: every reference to Velasari, V, Kaushik, `cognitive-memory`/CM naming, dated
   incidents (2026-08-29, 2026-09-14, "failed three times"), and specific memory ids
   (`935e77ad`, `4067a9fa`, `e9eb468a`, `fd829568`). Kept as mechanism, not story: the
   instance-ranks-over-procedure rule ("a rule can be re-derived from its story; a story
   cannot be re-derived from its rule"), the two-holders-breaks-boot reasoning for
   reserved tags, the persona/person-model distinction. Reserved tag holders are stated
   as "the one memory `/dream` maintains as the surface/self map" rather than fixed CM
   ids, since #3 is what creates those holder memories — this story only fixes the rule.
   Updated the Synaptra-specifics section for the verified `memory_store`/`memory_update`
   behaviour above; `rel_type` enum and per-type stability values verified against
   `synaptra/models.py` and `synaptra/decay.py` and match exactly.

2. **`.claude/skills/create-memory/SKILL.md`** — generalised from Velasari's, same
   treatment (no named people, no incident dates/ids, mechanism kept). Implements:
   recall-before-store handoff to `/update-memory` (AC 5), `source`/rater + tags +
   importance-only-above-0.8 (AC 6), verify id+type after store with `cm update --type`
   correction (AC 7), fact stored whole (AC 8), learning as instance+procedure with
   `supports` edge, same store type for both (AC 9), boundary node with `part_of` edge
   (AC 10), correction-as-`procedural`-learning, never `identity` (AC 11), reserved-tag
   refusal with the `-design` alternative (AC 12), refuse `memory_relate` on a
   short id before calling it (AC 26), stop when synaptra is unreachable, write nothing
   in its place (AC 27), report a non-readable-back write as "not landed" (AC 25).
   References the shapes file, restates none of it (AC 3, confirmed by the check script
   below).

3. **`.claude/shared/memory/check_shapes.py`** — stdlib-only script asserting AC 1, 2, 3,
   23. First run caught a real bug in the script itself: the AC 1 heading check used an
   exact `"### create"`-style substring match, which missed `person-model`'s
   `### 🔴 read` heading (emphasis marker, same operation). Fixed to match the operation
   word inside any level-3 heading rather than the literal string, then re-ran.

## Check script output (final, after the AC1 heuristic fix)

```
[PASS] AC1: all four shapes (fact, learning, persona, person-model) present with create/read/update/delete
[FAIL] AC2: read-memory: SKILL.md missing; update-memory: SKILL.md missing; delete-memory: SKILL.md missing
[PASS] AC3: create-memory point at the shapes file, restate nothing
[FAIL] AC23: direct calls found in: dream, heartbeat

2/4 of this script's criteria pass.
```

Matches action.md's own prediction exactly: fail on AC 2 (three of four skills don't
exist yet) and AC 23 (dream/heartbeat untouched this cycle, by design — their rewrite
is #4/#5 per assumption.md), pass on AC 1 and AC 3.

## Criteria met, out of 27

**Met, with a check shown to fail when broken:**
- **AC 1** — `check_shapes.py` fails if the shapes file or any shape's CRUD section is
  removed. Met.
- **AC 3** — `check_shapes.py` fails if `create-memory` stops pointing at the shapes
  file or starts restating a shape header. Met, scoped to the one skill that exists —
  the criterion's full text ("each of the four") stays open until AC 2 also holds.

**Implemented but not proved this cycle** (no scripted synaptra session run yet against
the scratch store — this is cycle 2's constraint, see next action.md):
AC 5, 6, 7, 8, 9, 10, 11, 12, 25, 26, 27 — all written into `create-memory`, none
exercised against a live (scratch) store yet. "The skill file says so" does not count
per observe.md; nothing here is claimed as met.

**Not started:** AC 2 (3 of 4 skills), AC 4 (CLAUDE.md Synaptra section), AC 13–22, 24.

**Number this cycle moves: 0 → 2 / 27**, both proved by `check_shapes.py`.

## AC 23 grep, current state

```
.claude/skills/dream/SKILL.md
.claude/skills/heartbeat/SKILL.md
```

Unchanged from baseline — expected; those two skills are #4/#5's rewrite, not this
story's, per assumption.md.

## Branch and time

Branch: `feature/2-memory-shapes` (`git branch --show-current`).
Cycle started 2026-09-19 ~15:59 IST, this log finalized before the 20-minute mark.

