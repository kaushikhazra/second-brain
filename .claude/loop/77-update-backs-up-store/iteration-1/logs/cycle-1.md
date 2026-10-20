# Cycle 1 — #77

**Reproduced on 1.6.1.** The check run against the unmodified updater: 7 of 8 fail. No store in
the backup; after a failed update's auto-rollback the store is still the migrated one.

**Fix.** `update_brain.py`: `backup_store` copies `.claude/synaptra-data` into `<backup>/_store`
after `stop_synaptra` and before the install, and notes `store_backed_up` in the backup metadata
once the copy is complete. `restore_store` (run by `--restore` and by auto-rollback, after the old
synaptra is reinstalled) moves the live store aside to `.claude/synaptra-data.replaced-<time>` —
named in the output — and copies the backup back. The file restore skips `_store`. SKILL.md names
the store in the update and restore lists.

**Criteria held: 8 of 8** (`checks/update/check_store_backup.py`); 5 removals each fail their
named ACs. Regression: `check_defect_fixes` 15/15, `check_r2_r3_r4_r5_r8` 10/10,
`check_keeps_edits` 31/31.

**Accepted, not fixed.** `--skip-synaptra` neither backs up nor restores the store (synaptra is
untouched in that mode). The `.replaced-*` folders accumulate until the owner deletes them.
Not tested live: a real 2.0.0 -> 2.1.1 install.

**For Kaushik.** `--restore` after days of use sets the store back to update time; memories written
since are in the `.replaced-*` folder, not lost, but not merged.
