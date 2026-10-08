# Action

Cycle 1's constraint: a brain with no learning capability passes AC 2 by opening the project's files when asked, so AC 2's check cannot fail with learning removed — nothing is learned, only looked up.

1. Build the learning in `manage`: on take-in (and on `learn <name>`), `projects.py learn` prints the raw material — `CLAUDE.md` (or that there is none), README, the `.claude/` tree (skills, rules), the hooks from `.claude/settings*.json`, top-level folders, and a fingerprint (commit + blob hashes of `CLAUDE.md`/README). The brain writes the learned record to `.claude/projects/<name>.md` (gitignored, machine-local, moves with the brain): purpose, method, conventions, code, tests, `.claude/` contents, hooks listed-not-adopted, fingerprint. `SKILL.md`: answer "what do you know about X" from the record.
2. Extend `check_context.py`:
   - `--mode takein` for AC 1 — the object: after the take-in session, the record exists and carries alpha's method, conventions, `.claude/` contents and the hook.
   - Make AC 2 discriminate: plant a distinctive fact only in the record (not in the clone) after take-in, then ask; the answer must carry the planted fact. With the record ignored (or the capability removed), it cannot.
3. Re-run `check_clone.py --all` (regression for #38).
