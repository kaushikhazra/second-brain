# Cycle 6

**Time:** 2026-09-19 17:17 +0530 (read via `date`)
**Branch:** `feature/2-memory-shapes` (confirmed via `git branch --show-current`)

## Criteria re-read from GitHub, before the diff and before cycle 5's log

27 acceptance criteria re-confirmed via `gh issue view 2 -R kaushikhazra/second-brain`,
unchanged.

## `assumption.md` re-read fresh, nothing new since cycle 5

No new commits on the branch since cycle 5's push (`7f71782`). One uncommitted change
carried in from between cycles: my own edit to `action.md` queuing the decay-table fix
Velasari decided over crosschat after reading cycle 5's log (relayed instruction, not a
file change to `assumption.md` itself).

## Round 0 — the decay-table fix (Velasari's decision, queued last session)

Re-verified the stability values fresh from `synaptra/decay.py` rather than trusting
cycle 1's cached numbers (they hadn't changed: `working` 0.04 · `episodic` 2.0 ·
`semantic` 14.0 · `procedural` 60.0 · `identity` 365.0 · `person` 90.0). Added a
`person` row and an "Initial stability (days)" column to `CLAUDE.md`'s decay table,
values identical to `memory-shapes.md`'s own stability line.

**Extended `check_shapes.py`'s AC 4 check** to compare the two files' numbers directly
— parses both tables/lines, fails on any missing or mismatched type. This closes the
exact gap cycle 5 flagged and left open: two sources of truth that could drift apart
now can't, silently, without the check catching it.

## Round 1 — the `PreToolUse` hook (AC 12, AC 26)

Researched the actual hook schema and protocol against real examples on this machine
rather than writing one from memory — several `.claude/settings.json` files under
`C:/Projects/.prune/` with working `PreToolUse` hooks. Confirmed: JSON on stdin
(`tool_name`, `tool_input`), exit 0 allows, exit 2 with a stderr message blocks and the
message reaches the session; `matcher` is a regex over tool names (alternation with
`|` is standard); command paths are relative to the project root, convention
`.claude/hooks/<name>.py`, invoked with a bare `python` on PATH (no venv needed for a
stdlib-only script).

Wrote `.claude/hooks/memory_guard.py`: blocks `mcp__synaptra__memory_store` /
`memory_update` carrying `self-map` or `surface-map` in `tags` (AC 12), and blocks
`mcp__synaptra__memory_relate` when `source_id` or `target_id` isn't a full uuid
(8-4-4-4-12 hex, AC 26). Added the `hooks.PreToolUse` block to `.claude/settings.json`
— it had none before; confirmed the merge kept `extraKnownMarketplaces` intact and the
file is valid JSON.

Wrote `.claude/shared/memory/check_hooks.py` per `assumption.md`'s Route 1 exactly:
invokes the hook script directly with a bad payload and a good one per criterion, plus
one unrelated-tool sanity check.

```
[PASS] AC12 bad payload blocked: exit=2, stderr="BLOCKED (AC 12): tag(s) ['self-map'] are reserved for the one memory they mark. A memory ABOUT that list takes the '-design' form instead ('self-map-design' / 'surface-map-design'), never the bare reserved tag."
[PASS] AC12 bad payload blocked (update): exit=2, stderr="BLOCKED (AC 12): tag(s) ['surface-map'] are reserved for the one memory they mark. A memory ABOUT that list takes the '-design' form instead ('self-map-design' / 'surface-map-design'), never the bare reserved tag."
[PASS] AC12 good payload allowed: exit=0
[PASS] AC26 bad payload blocked: exit=2, stderr="BLOCKED (AC 26): memory_relate requires FULL uuids on both ends (8-4-4-4-12 hex, 36 chars). Rejected: source_id='abcd1234'. An 8-char prefix or any other shortened id is refused before the call, not after."
[PASS] AC26 good payload allowed: exit=0
[PASS] unrelated tool unaffected: exit=0

6/6 of this script's criteria pass.
```

One real bug caught along the way: the check script's own path resolution to the hook
file was off by one `.parent` (copied the pattern without recounting the directory
depth from `.claude/shared/memory/` — three levels up to `.claude`, not two). Fixed,
re-ran, passed.

`/create-memory`'s own refusal prose for AC 12 and AC 26 (written in cycle 1) already
states both rules — confirmed, not re-added; the hook is the backstop, not the only
place either rule lives.

## Round 2 — `check_shapes.py`, confirming nothing regressed

```
[PASS] AC1: all four shapes (fact, learning, persona, person-model) present with create/read/update/delete
[PASS] AC2: all four skills present and load
[PASS] AC3: create-memory, read-memory, update-memory, delete-memory point at the shapes file, restate nothing
[PASS] AC4: CLAUDE.md states all three 'never call directly' prohibitions and points at all three writer skills; stability numbers match the shapes file for all 6 types
[PASS] AC23: clean — no direct calls outside the four memory skills

5/5 of this script's criteria pass.
```

## Criteria met, out of 27

**Met, with a check shown to fail when broken (16, up from 14):**
- AC 1, 2, 3, 4, 23 — `check_shapes.py`
- AC 6, 7, 9, 10, 25, 27 — `check_create_memory.py`
- AC 14 — `check_read_memory.py`
- AC 18, 19 — `check_update_memory.py`
- **AC 12, AC 26** — `check_hooks.py`, new this cycle. Unlike the earlier scratch-store
  proofs, these are the real thing per `assumption.md`'s own methodology — a mechanism
  (the hook) now genuinely enforces both rules at the tool-call boundary, not just a
  substrate-behaviour proxy for a skill's judgment.

**Implemented but not proved:** AC 5, AC 8, AC 11, AC 13, AC 15, AC 16, AC 17, AC 20,
AC 21, AC 22 — all remaining skill-judgment, no mechanism available (AC 8 has a
scripted-agent plan from `assumption.md`; the rest don't yet).

**Not started:** AC 24 (session-end conformance scan).

**Number this cycle moves: 14 → 16 / 27.**

## Branch and time

Branch: `feature/2-memory-shapes`. Cycle started 2026-09-19 17:17 IST, well inside the
23:30 fail-safe. Cadence 15 minutes (cron `42f55457`).
