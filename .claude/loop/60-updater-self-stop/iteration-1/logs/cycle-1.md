# Cycle 1 — #60

**Criteria held: 6 of 6.** `checks/update/check_venv_launch.py`: AC 1-6 PASS.

| Broken copy | Must fail | Result |
|---|---|---|
| `no-handover` (hand-over removed) | AC 3 | fails as required |
| `original-bug` (hand-over and self-exclusion removed) | AC 1, AC 6 | both fail as required (exit -1, no DONE, no named step) |

Regression: `check_defect_fixes.py` 15/15, `check_r2_r3_r4_r5_r8.py` 10/10,
`check_r7_manual_command.py` 10/10.

**Cause.** `stop_synaptra` stops every process whose executable sits under
`.claude\.venv`. Started with the venv's Python, the updater was one of them: it
killed itself before reinstalling synaptra and exited with no DONE and no failed step.

**Fix.** Two independent guards in `update_brain.py`:
1. `hand_over_to_standalone` — started from the venv, print one `MOVE` line and rerun
   under the interpreter in `.claude/.python`, before any backup. No PATH lookup.
2. `stop_synaptra` — walks up from its own PowerShell pid and never stops the updater
   or anything that launched it.

**Found on the way.** The `MOVE` line was buffered behind the child's output when
stdout is a pipe; it is now flushed, so it lands before BACKUP.

**Accepted rather than fixed.** If no standalone interpreter exists under
`.claude/.python`, the updater prints a NOTE and continues on the venv Python; guard 2
alone keeps it alive.

**For Kaushik.** None.
