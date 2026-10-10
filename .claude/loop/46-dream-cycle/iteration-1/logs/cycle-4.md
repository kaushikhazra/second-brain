# Cycle 4 — 2026-10-10 17:0x +0530

Branch: `feature/46-dream-cycle` (read from git). Issue #46 open, 11 ACs read first.

## Result

**Criteria met: 8 / 11.** Moved 8 → 8, deliberately.

| bucket | ACs |
|---|---|
| met | 1, 2, 3, 5, 6, 7, 8, 11 |
| mechanism proven, store run pending | 4, 9, 10 |
| UI-pending | none |

Why 4, 9 and 10 do not count yet: the skill, the CLI, the plan, the log and the falling
count are proved through a scratch brain by script (`check_dream_cycle_cli.py`, 15/15). But
the retype and archive themselves are done by `/update-memory` and `/delete-memory`, which
only the skill's text points at, and the counts handed to `finish` are the skill's own
report. Counting them would let the producer grade itself. They count once a real store
shows the backlog falling after the cycle's actions are applied.

## Built

- `src/.claude/skills/dream-cycle/SKILL.md`: `on`, `off`, `size`, `status`, one cycle by
  hand or from the heartbeat; hard stops (owner in conversation, synaptra unreachable); no
  backup step; skips boot-list ids and the handoff; archive never delete; merges and
  contradiction actions left for a hand `/dream`.
- `dream_cycle.py` gained the command line the skill drives (`on off size status plan-from
  batch finish`) and the log (`.claude/dream-cycle-log.md`, one line per cycle, same shape
  for hand and heartbeat). Log is machine-local: `update_brain.py` and `.gitignore`.
- `src/CLAUDE.md`: `/dream-cycle` in the lifecycle table and the structure table.
- `checks/dream-cycle/check_dream_cycle_cli.py`: 15 checks, 15 pass. Two vacuous clauses I
  had written (an always-true expression, a loop over an empty list) were replaced before
  the first run.

## Defect caught by the checks' own sweep, fixed this cycle

The formatter hook deletes an import it sees as unused the moment it is added, so adding
imports in one edit and the code using them in the next lost `import sys`, `argparse`,
`datetime` and three names from `activation`. The CLI check failed at the first batch call
and a smoke run showed `NameError: name 'sys' is not defined`. Imports re-added after the
code that uses them. The repo's existing undefined-name sweep (18 files clean) now covers
`dream_cycle.py`.

## Regression line

`check_dream_cycle.py` 23/23, `check_activation.py` 5/5 (includes the undefined-name sweep),
`checks/update/check_defect_fixes.py` 15/15. Heartbeat and curiosity checks not re-run: no
file they read changed this cycle.

## Still owed

- **The store run (AC 4, 9, 10):** against a scratch synaptra (port 8150, scratch DB), seed
  memories, take a real dry run, apply a batch of its promote and archive actions, re-run
  the dry run, assert the pending count fell and nothing was deleted.
- The mutation pass: each check shown to fail when its behaviour is removed.

## For Kaushik

- A cycle's counts come from the skill's own tally. The store run is what tests them, so
  until it runs I will not call 4, 9, 10 met.
- The session-start activation ask (repo convention for switch-on habits) is still not
  added; no criterion asks for it.
