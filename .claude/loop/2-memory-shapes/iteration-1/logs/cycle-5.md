# Cycle 5

**Time:** 2026-09-19 17:02 +0530 (read via `date`)
**Branch:** `feature/2-memory-shapes` (confirmed via `git branch --show-current`)

## Criteria re-read from GitHub, before the diff and before cycle 4's log

27 acceptance criteria re-confirmed via `gh issue view 2 -R kaushikhazra/second-brain`,
unchanged.

## `assumption.md` re-read fresh, nothing new

No new commits on the branch since cycle 4's push (`18119ec`), no uncommitted
mid-flight edits. `assumption.md` unchanged.

## Round 1 — `/delete-memory`, the last of the four skills

Read `C:/Projects/ai-persona/Velasari/.claude/skills/delete-memory/SKILL.md` in full.
Generalised the same way as the other three: no named people, no incident dates
(2026-08-29 appears twice, dropped to mechanism). Verified rather than assumed:
`memory_delete(confirm: bool, id, ids)` in this synaptra install genuinely refuses
without `confirm=true` (`server.py`, `"confirm must be true for permanent deletion"`)
— the source's claim holds here, written down as verified fact, same discipline as
every prior skill.

Implements: AC 21 (archive by default; delete only never-true or a duplicate, say
which), AC 22 (refuse removing one constellation node without the rest).

## Round 2 — `check_shapes.py`: AC 2 passes for the first time

```
[PASS] AC1: all four shapes (fact, learning, persona, person-model) present with create/read/update/delete
[PASS] AC2: all four skills present and load
[PASS] AC3: create-memory, read-memory, update-memory, delete-memory point at the shapes file, restate nothing
[PASS] AC23: clean — no direct calls outside the four memory skills

4/4 of this script's criteria pass.
```

## Round 3 — AC 4: `CLAUDE.md`'s Synaptra section

Per `assumption.md`'s scoping: replaced exactly the **Store / Update / Relate** bullets
under "CRITICAL — when to use" with routing to the four skills; added a **Remove**
bullet (the original had none at all — AC 4's text explicitly includes "removal," so
this was a gap to fill, not scope creep). Left the **Recall** and **Self** bullets
untouched — AC 4 is scoped to write/change/removal, not read, and `assumption.md`
named only Store/Update/Relate. Kept the tool list and the DB/install paragraphs
verbatim, as instructed. Also dropped the old inline type-picking heuristic ("event →
episodic, fact → semantic...") from the Store bullet — that logic now lives in
`.claude/shared/memory/memory-shapes.md`, and repeating a simplified version here would
be a second, drifting source of truth for exactly the kind of thing the shapes file
exists to own.

Verified with `grep` that `memory_store`, `memory_update`, `memory_delete` appear in
`CLAUDE.md` only in the tool list and inside a "Never call ... directly" sentence —
never as an instruction to call one.

**Extended `check_shapes.py` with an AC 4 check** rather than leaving this as a one-time
grep: asserts all three "Never call `memory_X` directly" prohibitions are stated and
all three writer skills are named. Fails if either regresses.

```
[PASS] AC1: all four shapes (fact, learning, persona, person-model) present with create/read/update/delete
[PASS] AC2: all four skills present and load
[PASS] AC3: create-memory, read-memory, update-memory, delete-memory point at the shapes file, restate nothing
[PASS] AC4: CLAUDE.md states all three 'never call directly' prohibitions and points at all three writer skills
[PASS] AC23: clean — no direct calls outside the four memory skills

5/5 of this script's criteria pass.
```

**Left alone, flagged rather than fixed:** `CLAUDE.md`'s "Memory types and decay" table
still lists five types (`working`/`episodic`/`semantic`/`procedural`/`identity`),
missing the `person` type cycle 1 verified exists in this synaptra install and that
`memory-shapes.md`'s own stability table already carries correctly. `assumption.md`'s
scoping note named only the Store/Update/Relate bullets and the tool-list/DB-install
paragraphs — this table wasn't named either way. Left untouched this cycle rather than
assumed in scope; a real second source of truth now exists between this table and the
shapes file's, and someone should decide whether to trim it or fix it.

## Round 4 — scratch-store proof for the archive/restore/delete mechanics

New scratch server (`SYNAPTRA_PORT=8051`, confirmed nothing already listening).
`.claude/shared/memory/check_delete_memory.py`:

```
[PASS] archive/restore mechanics: left active set=True, still reachable by memory_get=True, state after archive='archived', state after restore='active' -- this is the substrate behaviour /delete-memory's 'archive by default, reversible' promise depends on; it does not prove the skill always CHOOSES archive over delete (AC 21's actual judgment, unproved here)
[PASS] delete is permanent: memory_get after delete: not found, as expected

2/2 of this script's criteria pass.
```

**Neither line here counts toward the 27** — they prove the substrate mechanics
`/delete-memory` depends on (archive is reversible and leaves the record reachable;
delete truly removes it), not AC 21's actual judgment (which of never-true/duplicate/
outgrown applies, and archive-by-default as the skill's real default choice) or AC 22
(constellation-aware refusal), both still skill-level and unattempted. Recorded for
groundwork, not claimed as proof of a numbered criterion — same discipline as cycle 2's
AC 8 finding.

Scratch server stopped after the checks (confirmed via `netstat`/`taskkill`).

## Criteria met, out of 27

**Met, with a check shown to fail when broken (14, up from 12):**
- AC 1, AC 3 (all four skills), **AC 2** (new — all four skills exist and load, for the
  first time), **AC 4** (new — `CLAUDE.md` routes writes/changes/removals, checked by
  script), AC 23 — `check_shapes.py`
- AC 6, 7, 9, 10, 25, 27 — `check_create_memory.py`
- AC 14 — `check_read_memory.py` (empty-store slice)
- AC 18, AC 19 — `check_update_memory.py`

**Implemented but not proved:** AC 5, AC 8, AC 11, AC 12, AC 13, AC 15, AC 16, AC 17,
AC 20, AC 21, AC 22, AC 26 — all skill-judgment. AC 21/22 join this cycle (the
mechanics under them are now verified; the judgment itself is not).

**Not started:** AC 24 (session-end conformance scan).

**Number this cycle moves: 12 → 14 / 27.** All four skills, the shapes file, and
`CLAUDE.md`'s routing now exist — every remaining unproved-or-not-started criterion is
either a skill-judgment proof (needs the `PreToolUse` hook or a scripted-agent run per
`assumption.md`'s post-cycle-2 addendum) or AC 24 (session-end's scan, not yet
started).

## Branch and time

Branch: `feature/2-memory-shapes`. Cycle started 2026-09-19 17:02 IST, well inside the
23:30 fail-safe. Cadence 15 minutes (cron `42f55457`).
