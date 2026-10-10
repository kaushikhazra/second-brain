# Cycle 6 — 2026-10-10 17:4x +0530

Branch: `feature/46-dream-cycle` (read from git). Issue #46 open, 11 ACs read first.

## Result

**Criteria demonstrably met: 11 / 11.** Moved 1 → 11 (checks passing: 11 → 11).
Demonstrably = a check shown to fail when the behaviour is removed.

| AC | behaviour removed | killed by |
|---|---|---|
| 1 | the switch ignores off | `check_dream_cycle.py` AC1 |
| 2 | the batch size is not stored | AC2 |
| 3 | status drops `cycles_run` | AC3 |
| 4 | a cycle ignores the batch size | `check_dream_cycle_cli.py` AC4 |
| 5 | the gate ignores the switch | AC5, AC5b |
| 6 | the heartbeat does not name the dream cycle | AC6a |
| 7 | curiosity and the cycle may share a beat | AC7 |
| 8 | the gate ignores the owner being in conversation | AC8 |
| 9 | the apply calls removed (cycle 5) | `check_dream_cycle_store.py` AC9b, AC9c |
| 10 | a hand cycle is logged in a different shape | AC10 |
| 11 | `/update` would not carry the record; a restart loses it | AC11b, AC11a |

## What moved it

- `checks/dream-cycle/mutate.py`: copies `src` to scratch, removes one behaviour per
  criterion, runs the matching check against the copy (`DREAM_CYCLE_SRC`), and counts a
  mutation killed only if a check line **for that criterion** fails. A baseline run of the
  unmutated copy must be green first. Scratch copies are deleted after.
- First run: 10 of 11 killed. **AC 4 survived** in the sense that mattered: with the batch
  cap removed the CLI check crashed (it fed `STALE` to `json.loads`) instead of failing a
  labelled line. Fixed: `parse_batch` turns any non-list into an empty batch, so the broken
  cycle fails `AC4` on its own line. Second run: 11 of 11 killed.
- Both checks take the product root from `DREAM_CYCLE_SRC` (default: this repo's `src`).

## Regression line

All pass: `check_heartbeat.py` 3/3, `check_curiosity.py` 7/7, `check_dream.py` 5/5,
`check_news.py` 18/18, `check_activation.py` 5/5 (cycle 4, no change since), update
`check_defect_fixes.py` 15/15 (cycle 4), `check_r1_declaration.py` 5/5,
`check_r2_pinned_install.py` 5/5, `check_r2_r3_r4_r5_r8.py` 10/10, `check_r6_release_check.py`
10/10, `check_r7_manual_command.py` 10/10, `check_method_static.py` 13/13; dream-cycle
`check_dream_cycle.py` 23/23, `check_dream_cycle_cli.py` 15/15, `check_dream_cycle_store.py`
10/10 (cycle 5).

**Not run:** the multi-project checks that build a scratch brain and drive `claude -p`
(`check_context`, `check_clone`, the `_brain` ones), the two `*_scripted_agent` checks, and
`recall-session` / `local-agent`: forbidden here by Kaushik's no-spawned-`claude` rule, or
untouched by this loop. No file they read was changed.

## Accepted rather than fixed

- **Merge and contradiction actions** stay out of a cycle; the status counts them as needing
  a hand `/dream`. A backlog can floor above zero.
- **"Owner in conversation within 10 minutes"** is judged by the beat from the session; it
  has no mechanical clock.
- **The store run applies actions through the engine** (the same operations
  `/update-memory` and `/delete-memory` perform), not through those skills; the skills' own
  routing is proved by skill-text checks.
- **No session-start activation ask** for this habit, which the repo convention suggests
  for switch-on habits; no criterion asks for it.
- **No backup before a cycle**, Kaushik's ruling.

## For Kaushik

- Branch `feature/46-dream-cycle`, not merged. Merging is yours (or Velasari's).
- The cost risk stands: one real dry run a day on a 1000+ store does a vector search per
  memory. The once-a-day saved plan bounds it as you asked.

## Goal met

11/11. Commenting on #46 with the numbers, deleting the cron, reporting on crosschat.
