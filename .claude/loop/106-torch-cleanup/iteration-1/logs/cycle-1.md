# Cycle 1 — #106

Criteria read from `gh issue view 106`: 9.

Built `venv_cleanup.py` and called it from `run_update` after the rollback-guarded steps.
First run of `checks/update/check_torch_cleanup.py`: 13 of 23. The failures were one defect in my
design: I used uv's REQUESTED marker to tell an owner's install from a dependency, but uv writes it
on every package, so `sentence-transformers` read as "installed on purpose" and blocked every removal.
Next move came from that constraint: dropped the marker, narrowed the removal set to torch plus
sentence-transformers, and made any other package that requires either one a blocker.

Second run: 23 of 23 (AC 1-9, plus a mutation line for AC 3, 4, 5 and 6 that fails on a broken copy).
Existing checks: `check_r1_declaration` 5/5, `check_r2_r3_r4_r5_r8` 10/10, `check_store_backup` all PASS.

**For Kaushik**
- Packages the owner installed on purpose that require torch (torchvision, accelerate) block the
  cleanup rather than going with it. That leaves torch in place for those brains; it errs towards keeping.
- The import scan covers the brain's own code, not `projects/` clones. A clone that imports torch and
  runs on the brain's venv would not block. Accepted: clones are other people's code with their own envs.
- `--restore` reinstalls the old synaptra, which pulls torch back by its own requirements; the log and
  the printed command cover the manual route.
