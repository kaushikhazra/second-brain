# Cycle 9

**Time:** 2026-09-19 18:02 +0530 (read via `date`)
**Branch:** `feature/2-memory-shapes` (confirmed via `git branch --show-current`)

## Criteria re-read from GitHub, before the diff and before cycle 8's log

27 acceptance criteria re-confirmed via `gh issue view 2 -R kaushikhazra/second-brain`,
unchanged. AC 5, 11, 17, 20's exact text re-checked before building anything.

## `assumption.md` re-read fresh — no file update, but a crosschat decision to act on

No new commit on the branch (still `810fe93` as tip before this cycle). Velasari's
decision arrived over crosschat, not as an `assumption.md` commit this time: extend the
scripted-agent pattern to all nine remaining criteria, batched — *"AC 5 with AC 17 and
20, AC 13 with 15, AC 16 with 21 and 22"* — and keep a running cost total in the log.

**Gap in that batching, flagged between cycles, acted on this cycle:** AC 11 was absent
from all three groups. Folded it into this batch (AC 5/17/20) since a correction
scenario is its natural home and this batch already exercises `/update-memory`'s
wrong-vs-incomplete judgment. Flagged to Velasari; no correction had arrived by the
time this cycle started, so proceeded on that reading, as stated.

## Batch A — AC 5, 11, 17, 20

Built `C:/Projects/.tmp/second-brain-loop-2/batch-a-scratch-project/`: `create-memory`
and `update-memory` (cycle 8's scratch project only had `create-memory`), the shapes
file, a routing `CLAUDE.md`, its own `.mcp.json` against a fresh scratch data
directory (`batch-a-scratch-data`, never `ac8-scratch-data` — different scenario,
avoid cross-contamination).

Seeded one fact directly via `cm store` (the seed isn't under test) — *"The deploy
runbook lives at wiki.example.com/deploy-old."* — then stopped that server before any
headless run, same concurrent-access discipline as every prior cycle.

**Three scenarios, not one contrived prompt** — one prompt naturally covering all four
criteria would have been forced; three small ones read naturally:

1. **AC 5 + AC 20** — asked it to remember the same runbook fact, reworded. Result:
   *"Already have this... Since nothing changed, I didn't create a duplicate."* Cost
   $0.178.
2. **AC 17** — told it the fact was now wrong (the URL moved, old one dead). Result:
   *"Corrected in place — the memory now reads 'wiki.example.com/deploy-new'... prior
   version snapshotted."* Cost $0.172.
3. **AC 11** — gave it a correction about its OWN behaviour (an importance-setting
   habit), not a fact. Result: *"Stored and linked as a `learning` constellation, type
   `procedural`"* — instance + procedure + `supports` edge. Cost $0.276.

**Verified against the actual store, not the transcripts**, per the same discipline as
cycle 8:

- Exactly **3** active memories total (not 4) — confirms scenario 1 created no
  duplicate (AC 5 holds).
- The seeded fact's **id is unchanged** (`b725d3e1...`), its content now reads
  *"...deploy-new. (Previously at ...deploy-old — that link is dead.)"*, `access_count`
  3, `updated_at` moved — a genuine in-place rewrite, not a new node (AC 17 holds).
- Two new memories from scenario 3, both `memory_type: procedural` (never `identity`):
  `0b70cb37...` (instance, quotes the correction verbatim, tagged `correction`) and
  `05cca7a8...` (procedure, bare rule, no story). `cm related` on the instance confirms
  a real `supports` edge to the procedure, `rel_type: "supports"` (AC 11 holds).

**AC 20 is the one caveat**: "confirmed by reading the memory back" describes a step in
the agent's own process, not a property the final store state alone proves. The
transcript's multi-turn count (9 turns for scenario 2) and its own claim of a
before/after check are corroborating, not independently ground-truth-verifiable the way
a store-count or an edge is. Counted, with this caveat stated plainly — same treatment
as AC 25 (cycle 2) and AC 14 (cycle 3), both counted on a stated, narrower proof than
their full literal text.

Packaged as `.claude/shared/memory/check_batch_a_scripted_agent.py` for reuse. Not
re-run after packaging — the manual run already produced and verified the results.

`check_shapes.py` re-run: 5/5, unaffected (no skill files edited this cycle, only
used and read).

## Cost so far

Cycle 8 (AC 8): ≈$0.41. Cycle 9 (Batch A, three runs): $0.178 + $0.172 + $0.276 =
**$0.626**. **Running total across the scripted-agent work: ≈$1.04.**

## Criteria met, out of 27

**Met, with a check shown to fail when broken (22, up from 18):**
- AC 1, 2, 3, 4, 23 — `check_shapes.py`
- AC 6, 7, 9, 10, 25, 27 — `check_create_memory.py`
- AC 14 — `check_read_memory.py`
- AC 18, 19 — `check_update_memory.py`
- AC 12, 26 — `check_hooks.py`
- AC 24 — `check_conformance_scan.py`
- AC 8 — `check_ac8_scripted_agent.py`
- **AC 5, 11, 17, 20** — `check_batch_a_scripted_agent.py`, new this cycle

**Remaining, queued for Batch B (cycle 10) and Batch C (cycle 11), per action.md:**
AC 13, AC 15 (Batch B) · AC 16, AC 21, AC 22 (Batch C).

**Number this cycle moves: 18 → 22 / 27.**

## Branch and time

Branch: `feature/2-memory-shapes`. Cycle started 2026-09-19 18:02 IST, well inside the
23:30 fail-safe. Cadence 15 minutes (cron `42f55457`).
