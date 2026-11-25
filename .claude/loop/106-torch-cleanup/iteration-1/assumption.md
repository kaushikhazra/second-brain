# Assumptions — #106

- `update_brain.py` stays stdlib-only; the cleanup lives beside it in `venv_cleanup.py`.
- The cleanup never fails or rolls back an update (AC 5); it runs after the rollback-guarded steps.
- Removal set is torch and sentence-transformers only. Anything else that requires either keeps both.
- uv's REQUESTED marker is not a usable "installed on purpose" signal: uv writes it on every package.
- Managed project clones under `projects/` are not "the brain's own code" for the import scan.
