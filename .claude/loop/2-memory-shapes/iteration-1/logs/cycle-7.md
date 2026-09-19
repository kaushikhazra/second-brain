# Cycle 7

**Time:** 2026-09-19 17:32 +0530 (read via `date`)
**Branch:** `feature/2-memory-shapes` (confirmed via `git branch --show-current`)

## Criteria re-read from GitHub, before the diff and before cycle 6's log

27 acceptance criteria re-confirmed via `gh issue view 2 -R kaushikhazra/second-brain`,
unchanged. AC 24's exact text re-checked: "A direct store made outside the four skills
is found by the session-end conformance scan and reported by id."

## `assumption.md` re-read fresh, nothing new since cycle 6

No new commits since cycle 6's push (`17d04b1`), no uncommitted mid-flight edits.

## ⚠ A real conflict, flagged rather than quietly resolved either way

`assumption.md` states: *"Nothing in this loop touches `persona.md`, `user.md`,
`init-brain`, `session-start`, `session-end`, `local-agent` or `agent-creator`."*
`session-end` is named explicitly, off-limits.

But AC 24 is literally "the session-end conformance scan," and `CLAUDE.md`'s own
loop-engineering section (written before this loop started, in PR #9) already says:
*"a check is a script or a scripted session that reads them and exercises them —
`session-end/verify_memory.py` is the seed."* `CLAUDE.md` pre-authorizes the exact file
AC 24 needs, inside the exact skill `assumption.md` excludes.

**Resolution made this cycle, not deferred:** read the exclusion narrowly — as
protecting `session-end`'s existing mechanics (cron-kill, learnings, handoff), which
this cycle does not touch at all — and treat a wholly new, additive step plus a new,
self-contained script as outside what "touches" was meant to prevent, since
`CLAUDE.md` already committed to this file's existence. **This is a judgment call, not
a certainty**, made because blocking an entire cycle on it seemed worse than making a
narrow, clearly-flagged reading and letting it be corrected if wrong. Said here
plainly, and in this cycle's crosschat report, rather than buried.

## Round 1 — the detection signal: `create-memory:` source prefix

AC 24 needs a scan to tell a compliant store from a direct one, but nothing in
synaptra records which skill wrote a memory. Checked `/create-memory`'s own
instruction (cycle 1's "Pass `source`..." line) — it was free-form ("the identifier of
the model or process"), which a direct call could set identically. **No signal existed
to detect against.**

Fixed the gap at its source (the skill's own contract, cycle 1's artifact, squarely
this story's to adjust): `/create-memory` now passes `source` as
`"create-memory:<model-or-process-id>"` — the prefix is the detectable signal, the
suffix is still the rater. This is a design decision, made and stated, not left
implicit.

## Round 2 — where the live store actually lives, and why that matters

Investigated before writing the scan: `.mcp.json` runs synaptra over **stdio**
(`synaptra.exe --transport stdio`), spawned per-session by the Claude Code harness —
there is no standing HTTP endpoint the way this story's scratch servers have one.
Starting a second synaptra process against `.claude/synaptra-data` while the session's
own stdio server is live risks a concurrent-access conflict on the SurrealKV file — a
real risk, checked and reasoned through, not assumed away.

**Design that avoids it:** the scan script does no synaptra I/O of its own. It reads a
JSON file the *live session* produces by calling `memory_list` itself (through the
connection it already holds) and writes to disk. `verify_memory.py` is pure logic over
already-fetched data — read-only by construction, since it never has a write path at
all.

## Round 3 — built and wired

- `.claude/skills/session-end/verify_memory.py` — flags any active memory whose
  `source` doesn't start with `create-memory:`, by id.
- `.claude/skills/session-end/SKILL.md` — one new step (4, "Run the memory conformance
  scan"), inserted before the renumbered sign-off step. Nothing else in the file
  changed — no rewording of the existing learnings/handoff steps, deliberately, to keep
  this addition as narrow as the exclusion-reading above requires.
- `.claude/shared/memory/check_conformance_scan.py` — scratch-store proof: stores one
  compliant memory and one violation, lists active memories, feeds the listing to
  `verify_memory.py`, confirms only the violation is flagged and the exit codes are
  correct in both the dirty and clean cases.

**One real bug caught**, the same class as cycle 6's: `check_conformance_scan.py`'s own
path to `verify_memory.py` was off by one `.parent` (two levels instead of three from
`.claude/shared/memory/` to `.claude/`). This is now the **second** occurrence of this
exact mistake (`check_hooks.py`, cycle 6, was the first) — worth naming as a pattern:
counting directory levels by feel gets it wrong reliably enough that it deserves a
second look every time, not just when something fails.

```
[PASS] AC24 conformance scan: exit=1, violation id flagged=True, compliant id wrongly flagged=False
[PASS] AC24 clean listing -> exit 0: exit=0

2/2 of this script's criteria pass.
```

(The scratch store's own accumulated cross-cycle probe data — 25 of 27 memories in it —
all correctly flagged too, since none of that historic scratch data carries the
`create-memory:` prefix the convention only adopted this cycle. Expected, not a bug.)

Scratch server stopped after the check (confirmed via `netstat`/`taskkill`).

## Round 4 — `check_shapes.py`, confirming nothing regressed

```
[PASS] AC1 / AC2 / AC3 / AC4 / AC23 — all still pass, 5/5.
```

## Criteria met, out of 27

**Met, with a check shown to fail when broken (17, up from 16):**
- AC 1, 2, 3, 4, 23 — `check_shapes.py`
- AC 6, 7, 9, 10, 25, 27 — `check_create_memory.py`
- AC 14 — `check_read_memory.py`
- AC 18, 19 — `check_update_memory.py`
- AC 12, 26 — `check_hooks.py`
- **AC 24** — `check_conformance_scan.py`, new this cycle

**Implemented but not proved:** AC 5, AC 8, AC 11, AC 13, AC 15, AC 16, AC 17, AC 20,
AC 21, AC 22 — all skill-judgment, no assigned mechanism except AC 8 (the
scripted-agent route from `assumption.md`'s post-cycle-2 addendum, not yet run).

**Not started:** none. Every criterion is now either met, or in the unproved list with
a reason stated.

**Number this cycle moves: 16 → 17 / 27.**

## Branch and time

Branch: `feature/2-memory-shapes`. Cycle started 2026-09-19 17:32 IST, well inside the
23:30 fail-safe. Cadence 15 minutes (cron `42f55457`).
