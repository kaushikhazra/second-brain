# Action

Cycle 2's constraint: AC 4's check cannot tell the ALREADY_MANAGED branch from git refusing to clone into an existing folder; AC 5, 6, 7 have no check.

1. Strengthen `--mode again`: fail if the stream holds any `git clone` call or `projects.py clone` output other than `STATUS: ALREADY_MANAGED`, and if the reply reads as a failure. Demonstrate it fails with the ALREADY_MANAGED branch removed from the scratch brain's copy of `projects.py`.
2. Add `--mode fail` for AC 5 — three owner turns: unreachable (`https://no-such-host-xyz.invalid/a/b.git`), missing access (alpha's SSH URL — this machine has no GitHub key), not a git repo (`https://example.com/`). Verify each reply's message is distinct from the other two and no folder is left under `projects/`.
3. Add `--mode list` for AC 6 (reply names each project's path and origin) and `--mode relocate` for AC 7 (copy the scratch brain to a renamed folder, ask it to list and to take alpha in again; it must find the existing clone at the new path).

Run every mode fresh.
