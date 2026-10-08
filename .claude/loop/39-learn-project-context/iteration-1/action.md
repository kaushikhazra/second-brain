# Action

Cycle 2's constraint: AC 3, 4, 5, 6 have no check. AC 1 and 2 hold.

Extend `check_context.py`, run each mode fresh, then show each fails with its behaviour removed (scratch copy only, restored after):

1. `--mode nofile` (AC 3): take beta in (no CLAUDE.md). Reply says it has no CLAUDE.md; the record says so and its Purpose/Code sections come from beta's README and folders (`src/notes.py`).
2. `--mode hooks` (AC 6): from `takein`'s run — the reply lists alpha's `mark_session` hook and says it is not adopted; the scratch brain's own `.claude/settings.json` gained no hook; no `alpha-hook-fired.log` appears under the brain.
3. `--mode upstream` (AC 4) + AC 5 in the same turn: make "upstream" a local bare mirror of alpha (`git clone --bare`, then `remote set-url` on the scratch clone — never push to the real sandbox). Commit a CLAUDE.md change to the mirror adding one rule (e.g. "Every new function carries a docstring starting with 'Returns'"). Owner asks for a small change in alpha ("add a farewell(name) function"). Grade: before any file is edited in the clone, the record's `claude_md` equals the new blob and mentions the new rule (AC 4); a spec appears under the clone's `.claude/specs/` before code changes (alpha's method won over the brain's loops), and the reply names which rule applied (AC 5).
4. Re-run `check_clone.py --all` (#38 regression).
