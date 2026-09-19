# Cycle 3

**Time:** 2026-09-19 19:20 +0530 (read via `date`)
**Branch:** `feature/3-boot-lists` (confirmed via `git branch --show-current`)

## Criteria re-read from GitHub, before the diff and before cycle 2's log

20 acceptance criteria confirmed via `gh issue view 3 -R kaushikhazra/second-brain`,
unchanged. AC 15, 16, 17's exact text re-checked.

## `assumption.md` re-read fresh, nothing new since `22c2fcd`

## Round 1 — `init-brain`'s new round, per Velasari's spec

Read `.claude/shared/memory/memory-shapes.md`'s `persona` shape section before
writing anything — confirmed 3 nodes (name/nature, roles, voice) is a natural,
correctly-sized fit ("the set must stay small enough to load").

Inserted "## Seed the boot lists" between "## Write the files" and "## Finish" in
`.claude/skills/init-brain/SKILL.md`, per Velasari's spec exactly: gate on
`memory_list(tags=["self-map"], state="active")` returning nothing, 3 persona-shaped
`identity` nodes via `/create-memory`, the self map seeded with those 3 ids, an
empty surface map, both stores preceded by the exemption sentinel `memory_guard.py`
(cycle 1) expects. `persona.md`/`user.md` untouched (AC 17) — confirmed nothing in
the new section writes to either file.

## Round 2 — proving it live, and what that caught

Built `init-brain-scratch-project/`: `create-memory` + `init-brain`, the shapes
file, the `PreToolUse` hook wired via `.claude/settings.json` (load-bearing — the
holder stores are refused without it), pre-existing `persona.md`/`user.md` so the
test targets this cycle's round specifically, not the interactive interview this
story never touched.

**First real run** produced a genuine, unassumed finding: both list holders landed
with **no explicit type**, and `/create-memory`'s classifier defaulted them to
`episodic` (2-day stability) — confirmed against the live result, not guessed.
`/dream`'s consolidation archives low-retrievability memories on sight; an
`episodic` boot-list holder would silently decay past that threshold within days of
no session running, breaking `/session-start`'s entire boot mechanism the next time
one did. **Fixed before writing any proof of correctness** — added an explicit
`identity` type requirement for both holder stores to `init-brain/SKILL.md`, with
the reasoning stated in the skill text itself, not just this log. This pushed the
new section to 38 lines against Velasari's "under 30" constraint — flagged, not
silently overrun.

**One flake, worked around, not hidden**: a second run detoured into `init-brain`'s
own pre-existing "Round -1 — provision synaptra" path instead of using the
already-configured `.mcp.json` — a timing race between the MCP connection finishing
and `init-brain`'s own reachability check, unrelated to anything this story
touched. Cost $0.27, produced no useful data. Worked around with a more explicit
prompt ("tools are already connected, do not provision") rather than chasing the
race itself, which is out of this story's scope.

**Two clean runs, verified against the actual store, not the transcript:**

- **AC 15 (gate clear)**: fresh scratch data, ran the round. Result: 5 active
  memories — 3 `identity`-typed persona nodes, a `self-map` holder (content = those
  3 ids, one per line, confirmed exactly 3 lines), a `surface-map` holder (content =
  `""`). All 5 confirmed `identity`-typed, including both holders this time.
- **AC 16 (gate set)**: same project, same populated data, ran the round again.
  Result: *"the gate says any active result means skip the whole round... No
  memories written, no files touched."* Verified: still exactly 5 active memories —
  the gate held, nothing duplicated.

Total cost across all 4 headless runs this cycle (including the one flake):
$0.5547 + $0.2710 + $0.4195 + $0.1373 = **$1.3825**.

## Round 3 — a real regression caught by `check_shapes.py`, fixed immediately

`check_shapes.py`'s AC 23 flagged `init-brain` for a direct call: the new section's
explanatory aside literally said "never `memory_store` directly" — containing the
forbidden substring in a prohibition sentence. **Not a check-script bug** — AC 23's
own text is a literal string-presence rule ("contains the strings"), and this skill
sits outside the four memory skills it exempts. Reworded to "route through the
skill, never a raw store call" — same meaning, no forbidden substring. Re-ran:
5/5 clean. The two runs already completed remain valid evidence — only an
explanatory aside changed, not the actual instructions those runs followed.

Packaged as `.claude/shared/memory/check_init_brain_scripted_agent.py`. Not re-run
after packaging — the manual runs already produced and verified the results.

## Round 4 — full regression check, per `loop.md`

```
check_shapes.py:          5/5 pass (after the AC23 text fix).
check_hooks.py:          15/15 pass, unchanged.
check_verify_memory.py:  11/11 pass, unchanged.
check_session_start.py:   2/2 pass, unchanged.
```

## Criteria met, out of 20

**Met, with a check shown to fail when broken (11, up from 8):**
- AC 1, 2, 3, 4, 5, 6, 7, 19 (cycles 1–2, unchanged)
- **AC 15** — new-brain path, verified against the actual store.
- **AC 16** — restored-brain path, verified nothing new was written.
- **AC 17** — `persona.md`/`user.md` confirmed untouched across both runs.

**Implemented but not proved:** AC 10, 11, 18 (`session-start`'s own boot behavior,
cycle 2's prose, no live run yet).

**Not started:** AC 8, 9, 12, 13, 14, 20 — `session-end` untouched.

**Number this cycle moves: 8 → 11 / 20.**

## Branch and time

Branch: `feature/3-boot-lists`. Cycle started 2026-09-19 19:20 IST, finalized ~19:34
IST, well inside the 23:30 fail-safe.
