# Cycle 2 — 2026-10-10 16:3x +0530

Branch: `feature/46-dream-cycle` (read from git). Issue #46 open, 11 ACs read first.

## Result

**Criteria met: 4 / 11.** Moved 0 → 4.

| bucket | ACs |
|---|---|
| met | 1 (switch on/off recorded), 2 (batch size stored, survives a switch, 0 refused), 3 (status: active, batch_size, cycles_run, backlog), 11 (state survives a fresh process; the record and the saved plan are in `update_brain.py` MACHINE_LOCAL) |
| pending | 4, 5, 6, 7, 8, 9, 10 |
| UI-pending | none |

Counted conservatively: AC 4, 5, 7, 8 have their gate proved (truth table passes) but the
heartbeat does not yet say to use it, so the owner-facing behaviour is not there.

## Built

- `src/.claude/shared/dream_cycle.py`: `switch`, `set_batch_size`, `status`,
  `record_cycle`, `should_run`, plus the saved-plan half (`new_plan`, `next_batch`,
  `mark_applied`, `plan_is_stale`, `load_plan`, `save_plan`). Plans only `promote` and
  `archive`; merge and contradiction actions are counted as `needs_dream`.
- `.claude/dream-cycle-plan.json` added to `update_brain.py` MACHINE_LOCAL and to
  `src/.gitignore` (Kaushik's once-a-day design note).
- `checks/dream-cycle/check_dream_cycle.py`: 19 checks, 16 pass. The 3 that fail are the
  heartbeat wiring (AC 6a, 6b, 7b).

## Regression line

`check_heartbeat.py` and `check_curiosity.py` (cycle 1, unchanged files), `check_activation.py`
5/5, `checks/update/check_defect_fixes.py` 15/15 (touched `update_brain.py`). The rest of
`checks/` is re-run in the cycle that touches its files. No regression.

## Not yet proven

The new checks pass; they have not yet been shown to fail when the behaviour is removed.
That mutation pass is owed before convergence (observe.md's definition of "demonstrably").

## For Kaushik

- Repo convention says anything the owner switches on is asked once at `/session-start` and
  again after a VERSION change. The issue has no criterion for it. Adding a `dream_cycle`
  row to session-start's activation table is cheap; I will do it in a later cycle unless told
  not to.
- A hand-run cycle counts the same as a heartbeat one even while the switch is off (AC 10);
  `record_cycle` does not check the switch. The gate sits in the heartbeat only.
