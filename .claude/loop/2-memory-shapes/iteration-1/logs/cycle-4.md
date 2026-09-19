# Cycle 4

**Time:** 2026-09-19 16:47 +0530 (read via `date`)
**Branch:** `feature/2-memory-shapes` (confirmed via `git branch --show-current`)

## Criteria re-read from GitHub, before the diff and before cycle 3's log

27 acceptance criteria re-confirmed via `gh issue view 2 -R kaushikhazra/second-brain`,
unchanged.

## `assumption.md` re-read fresh, nothing new

No new commits on the branch since cycle 3's push (`6824fd6` is still the tip before
this cycle's work), no uncommitted mid-flight edits. `assumption.md` unchanged from
cycle 3's reading.

## Round 1 — `/update-memory`

Read `C:/Projects/ai-persona/Velasari/.claude/skills/update-memory/SKILL.md` in full.
Generalised the same way as the prior three: no named people, no incident dates
("four times in a single afternoon", "2026-08-29"), mechanism kept. One correction
carried forward from cycle 1's verified finding: the source claims `memory_update`
"ignores `memory_type` entirely" — this synaptra install's engine does apply it (cycle
1's reading of `engine.py`). Wrote the skill's mechanics section to state the `cm`-CLI
path as the correct mechanism *because* it's the documented AC 19 path and keeps type
corrections visible in `cm`'s own history, not by repeating the now-inaccurate "ignores
it entirely" claim.

Implements: AC 16 (refuse a tidiness-only update, say why — the stability-reinforcement
mechanics justify this), AC 17 (wrong → rewrite in place; incomplete → new node + edge),
AC 18 (fetch current tags first, pass the full intended set), AC 19 (`cm update --type`,
confirmed by read-back), AC 20 (verify every update by reading the memory back, not the
return value). Points at the shapes file, restates nothing.

## Round 2 — check_shapes.py

```
[PASS] AC1: all four shapes (fact, learning, persona, person-model) present with create/read/update/delete
[FAIL] AC2: delete-memory: SKILL.md missing
[PASS] AC3: create-memory, read-memory, update-memory point at the shapes file, restate nothing
[PASS] AC23: clean — no direct calls outside the four memory skills

3/4 of this script's criteria pass.
```

One skill left for AC 2.

## Round 3 — scratch-store proof for AC 18 and AC 19

New scratch server, same pattern (`SYNAPTRA_PORT=8051`, scratch data dir, confirmed no
prior listener on the port first). Wrote `.claude/shared/memory/check_update_memory.py`.

```
[PASS] AC18: before=['tag-a', 'tag-b'], after update(tags='tag-a,tag-c')=['tag-a', 'tag-c'] -- 'tag-b' dropped=True (not renamed, not preserved) confirms wholesale replace; the skill's fetch-current-tags-first step is what AC 18 actually requires
[PASS] AC19: stored as 'episodic', 'cm update --type procedural' then read back as 'procedural' -- the cm-CLI path works and is confirmed by re-read, not by the update call's own return value

2/2 of this script's criteria pass.
```

AC 19's check is the closest match yet between a check and its criterion's literal
text — it performs exactly the operation the criterion describes. AC 18's check proves
the substrate mechanic the skill's "fetch current tags first" instruction exists to
guard against; it does not prove the skill always does that fetch (same caveat class as
AC 6/7/9/10 in cycle 2).

Scratch server stopped after the check (`taskkill`, confirmed via `netstat` before
starting — no leaked listener on 8051).

AC 16, 17, 20 not attempted this cycle — all skill-judgment (when an update is "only
tidiness," whether something is "wrong" vs "incomplete," confirming by re-read is a
discipline the skill either follows or doesn't). Added to the unproved list rather than
forced.

## Criteria met, out of 27

**Met, with a check shown to fail when broken (12, up from 10):**
- AC 1, AC 3 (now covering three skills), AC 23 — `check_shapes.py`
- AC 6, 7, 9, 10, 25, 27 — `check_create_memory.py` (unchanged)
- AC 14 — `check_read_memory.py` (unchanged, empty-store slice)
- **AC 18, AC 19** — `check_update_memory.py`, new this cycle

**Implemented but not proved:** AC 5, AC 8, AC 11, AC 12, AC 13, AC 15, AC 16, AC 17,
AC 20, AC 26 — all skill-judgment, unchanged reasoning from prior cycles.

**Not started:** AC 2 (one of four skills — `delete-memory`), AC 4, AC 21–22, AC 24.

**Number this cycle moves: 10 → 12 / 27.**

## Branch and time

Branch: `feature/2-memory-shapes`. Cycle started 2026-09-19 16:47 IST, well inside the
23:30 fail-safe. Cadence 15 minutes (cron `42f55457`).
