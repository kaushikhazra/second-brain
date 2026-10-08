# Action

Cycle 3's constraint: AC 4, 6 and 7 pass but have no fails-when-removed demonstration, and the passing runs predate cycle 3's product fixes.

1. Full fresh proof: `--build`, then `--run` + `--verify` for every mode in order (https, again, fail, list, relocate).
2. Demonstrate each check fails with its behaviour removed — edit only the scratch brain's copy, re-run that mode, then restore with a rebuild:
   - AC 4: delete the ALREADY_MANAGED branch from the scratch `projects.py` → expect `again` to FAIL.
   - AC 6: remove the `list` subcommand and every mention of listing from the scratch `manage/SKILL.md` and routing row → record honestly whether the owner can still list (if the brain improvises a correct list, say so in the log; the behaviour the owner gets is what is graded).
   - AC 7: in the moved brain's `projects.py`, replace `brain_root()` with the ORIGINAL brain's absolute path, and delete the original's `projects/` first → expect `relocate` to FAIL.
3. If 7/7 (SSH half manual-test) holds with every demonstration: close per `loop.md`.
