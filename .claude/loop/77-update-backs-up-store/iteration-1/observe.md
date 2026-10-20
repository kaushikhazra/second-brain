# Observe — #77

`python checks/update/check_store_backup.py` — drives the real run_update / restore_backup
with the stop/install/verify calls replaced (the fake install migrates the store), then removes
one behaviour at a time and requires the named AC to fail. Done = 8 of 8 hold and every removal
is caught. Regression: `check_defect_fixes.py`, `check_r2_r3_r4_r5_r8.py`, `check_keeps_edits.py`.
