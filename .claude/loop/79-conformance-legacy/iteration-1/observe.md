# Observe — #79

`python checks/session-end/check_conformance_baseline.py` — runs the real verify_memory.py on
listings with legacy, direct and conforming memories, and the real run_update / restore_backup
(--skip-synaptra) for the baseline file; then removes one behaviour at a time and requires the
named AC to fail. Done = 8 of 8 hold and every removal is caught.
Regression: `.claude/shared/memory/check_verify_memory.py`, `checks/update/check_defect_fixes.py`,
`check_r2_r3_r4_r5_r8.py`.
