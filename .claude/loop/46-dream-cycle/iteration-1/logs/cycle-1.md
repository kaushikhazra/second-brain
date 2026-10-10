# Cycle 1 — 2026-10-10 16:2x +0530

Branch: `feature/46-dream-cycle` (read from git). Issue criteria read first from #46: 11 ACs.

## Result

**Criteria met: 0 / 11.** (met 0 · pending 11 · UI-pending 0)
Moved: 0, as planned. This cycle built the red check and settled the two open assumptions.

Regression line (the two checks nearest the files this loop touches): `check_heartbeat.py`
3/3 pass, `check_curiosity.py` 7/7 pass. The rest of `checks/` is re-run in the cycle that
touches its files.

## Assumptions settled from synaptra's source (projects/synaptra, v2.1.1)

1. **A consolidation run cannot be capped.** `memory_consolidate(dry_run)` takes only
   `dry_run`; the engine runs decay, promotion, archive and merge over every active memory.
   So the batch size is applied by the cycle, not by synaptra.
2. **The backlog is the pending action list.** `memory_consolidate(dry_run=true)` returns
   the actions the pipeline would take: `promote` (retype), `archive`, `merge`,
   `flag_contradiction`. Backlog = count of pending `promote` + `archive`.
3. **A cycle applies only the reversible actions**, individually, up to `batch_size`:
   `promote` through `/update-memory` (type change), `archive` through `/delete-memory`
   (archive). `merge` rewrites the primary's content and `flag_contradiction` adds edges;
   both are left to a hand `/dream` and reported as "needs /dream" in the status. Kaushik's
   rule: archive, never delete.
4. Boot-list ids and the current handoff are skipped and reported, as `/dream` Act 2 does.

## Design (state and gate)

New `.claude/shared/dream_cycle.py`, pure functions over the activation record, habit key
`dream_cycle`: `switch`, `set_batch_size`, `status`, `record_cycle`, `should_run`. The
record already survives `/update` (`update_brain.py` MACHINE_LOCAL). New skill
`.claude/skills/dream-cycle/` runs one batch; heartbeat gets a `dream-cycle` section in
`observe.md` and `goal.md` beside `quiet-cycles`.

## Built

`checks/dream-cycle/check_dream_cycle.py` — 12 checks, 1 passes (AC11b: the record is
already machine-local). The module and the heartbeat section do not exist yet.

## For Kaushik

- **Cost:** the dry-run consolidation does a vector search for every active memory on each
  cycle, so on a store of over a thousand memories each cycle has a real cost. If it is
  too slow on quiet beats, the fix is a cheaper selection (archive/promote candidates only),
  not a bigger interval.
- **Merge and contradiction actions stay out** of the cycle, so the backlog count can
  shrink to a floor that only a hand `/dream` clears. The status will say so.
