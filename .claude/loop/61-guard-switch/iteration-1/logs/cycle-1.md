# Cycle 1 — #61

**Criteria held: 6 of 6.** `checks/guard/check_guard_switch.py`: AC 1-6 PASS.

| Broken copy | Must fail | Result |
|---|---|---|
| hook ignores the switch | AC 1, 3, 5 | all fail |
| hook defaults to on | AC 5 | fails |
| `/guard` writes nothing | AC 1 | fails |
| no off line | AC 4 | fails |
| session-start skips the line | AC 4 | fails |
| update forgets the guard | AC 6 | fails |
| update overwrites the owner's choice | AC 2 | fails |

Regression: `checks/update/*` 15/15, 10/10, 10/10; `guard/test_unwrap.py` 14/14;
`guard/check_guard.py` 11 of 12 — AC 8 fails identically on `main` (the scorecard is
not on this machine), so unchanged.

**Design.** The setting is the `guard` entry of `.claude/activations.json`, written by
`/guard` through `shared/activation.py` like `/curiosity` and `/news`. The hook reads it
inline (stdlib, no import from `shared`, so copies of the hooks folder still work) and
returns before loading weights when it is not `active: true`. No record, no entry or an
unreadable file mean off, which is what makes a new brain start off with nothing to
provision. An updated brain that had `command_guard.py` and no entry gets `guard: on`
written by `update_brain.py`; `--restore` takes that entry out again.

**Found on the way.** The first version left the entry behind on `--restore`, which
broke `check_defect_fixes` D1 (update then restore byte-identical, 14/15). Fixed by
noting the added entry in the backup; back to 15/15.

**Accepted rather than fixed.**
- A brain that never had the guard (no `command_guard.py` before the update) gets no
  entry, so the guard is off after the update.
- A corrupt `activations.json` reads as guard off, for every habit's record alike.
- `/guard` is not asked about at session start; the off line is the only prompt.
- The `guard` record shape is written in two places outside `activation.py`
  (`update_brain.py` and the hook's read), because both are stdlib-only standalone files.

**For Kaushik.** Only `command_guard.py` is switched; `memory_guard.py` stays on, since
#61 names the command guard.
