# Cycle 3

**Time:** 2026-09-19 16:32 +0530 (read via `date`)
**Branch:** `feature/2-memory-shapes` (confirmed via `git branch --show-current`)

## Criteria re-read from GitHub, before the diff and before cycle 2's log

27 acceptance criteria re-confirmed via `gh issue view 2 -R kaushikhazra/second-brain`,
unchanged.

## `assumption.md` re-read fresh at the top of this cycle, per discipline

Picked up two things landed between cycles, both already on disk (no fetch needed —
Velasari commits directly to this shared working tree):

- **`2a7a7b5`** — how to prove AC 8/12/26: AC 12 and AC 26 become a `PreToolUse` hook
  in `.claude/settings.json` (mechanism, not judgment); AC 8 needs a headless
  `claude -p` scripted-agent run. Both deferred to whichever cycle touches
  `.claude/settings.json` — not this one.
- **Interval change, relayed from Kaushik, applied between cycle 2 and this cycle** (not
  part of this cycle's work, logged for the record): cron `afdc3277` (every 20 min)
  deleted, replaced with `42f55457` (every 15 min), same prompt. `loop.md` was already
  edited on disk to say 15 minutes; committing it with this cycle as instructed.

## Round 1 — `/read-memory`

Read `C:/Projects/ai-persona/Velasari/.claude/skills/read-memory/SKILL.md` in full.
Generalised the same way as `create-memory`: no named people, no incident dates, no CM
ids, mechanism kept. Two things did NOT port as-is, decided rather than defaulted:

- **The `/recall-session` fallback step.** Second brain's `CLAUDE.md` Structure table
  has no such skill (checked before assuming). Dropped; replaced with "say the miss
  plainly, don't fabricate an answer, don't claim non-existence" — which is just AC 14
  stated as an instruction.
- **The negative-strength-edge / "curiosity" section.** Nothing in `CLAUDE.md`, `dream`,
  or `heartbeat` creates or expects such edges in this repo. Left out entirely rather
  than describing a mechanism that doesn't exist here.

Implements: AC 13 (tool ladder + "say which tool was used"), AC 14 (null result
reported as not-found), AC 15 (pull the boundary before applying a learning's rule).
Points at the shapes file, restates nothing.

## Round 2 — check_shapes.py

```
[PASS] AC1: all four shapes (fact, learning, persona, person-model) present with create/read/update/delete
[FAIL] AC2: update-memory: SKILL.md missing; delete-memory: SKILL.md missing
[PASS] AC3: create-memory, read-memory point at the shapes file, restate nothing
[PASS] AC23: clean — no direct calls outside the four memory skills

3/4 of this script's criteria pass.
```

Matches action.md's expectation: AC 2 still fails (two skills remain), AC 3 now covers
both existing skills.

## Round 3 — a real finding about `memory_recall`, before writing AC 14's check

Tried to prove AC 14 ("a recall that returns nothing") against the cycle-2 scratch
store (populated with ~10 test memories). **It cannot be produced there.**
`memory_recall`'s ranked fusion returns a best-effort, non-empty result for *any*
query — a nonsense string, an impossible tag filter — always with a non-zero score.
Confirmed the `--tags` filter on `recall` is a ranking signal, not a hard filter: a
recall filtered to a tag no memory carries still returned ten unrelated results.

Started a **second** scratch server against a genuinely empty data directory
(`C:/Projects/.tmp/second-brain-loop-2/empty-data`, port 8052) and recalled there:
`{"success": true, "data": {"memories": []}}` — clean, no error. **A literal empty
result exists only when the store itself is empty.** On a populated store, deciding
that a low-score hit "isn't really a match" is the skill's own judgment call — same
class as AC 5/8/11/12/26, not something a script can credit to synaptra.

Wrote `.claude/shared/memory/check_read_memory.py` proving exactly this slice:

```
[PASS] AC14 (empty-store slice): success=True, memories=[] -- clean empty list, no error

1/1 of this script's criteria pass.
```

Both scratch servers (8051, 8052) stopped after the checks — confirmed via
`netstat`/`taskkill`, no leaked process for cycle 4.

## Criteria met, out of 27

**Met, with a check shown to fail when broken (10, up from 9):**
- AC 1, AC 3 (now covering two skills), AC 23 — `check_shapes.py`
- AC 6, 7, 9, 10, 25, 27 — `check_create_memory.py` (cycle 2, unchanged)
- **AC 14** — `check_read_memory.py`, same treatment as AC 25 in cycle 2: the
  mechanical case the criterion describes (a null retrieval, representable and
  error-free) is proved; the skill's exact reporting phrasing is not directly
  testable by script, same as AC 25's positive-path-only proof. Counted for
  consistency with that precedent, caveat stated plainly rather than silently.

**Implemented but not proved:** AC 5, AC 8, AC 11, AC 12, AC 13, AC 15, AC 26 — all
skill-judgment criteria a raw script cannot exercise; AC 12/26 have a concrete plan
(the `PreToolUse` hook) and AC 8 has one (the headless scripted-agent run), both
deferred to a cycle that touches `.claude/settings.json` or runs a scripted agent.

**Not started:** AC 2 (two of four skills), AC 4, AC 16–22, AC 24.

**Number this cycle moves: 9 → 10 / 27.**

## Branch and time

Branch: `feature/2-memory-shapes`. Cycle started 2026-09-19 16:32 IST, well inside the
23:30 fail-safe. Cadence is now 15 minutes (cron `42f55457`), not 20.
